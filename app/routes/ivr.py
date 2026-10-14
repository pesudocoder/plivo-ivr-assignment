"""Plivo XML webhooks for the IVR call flow: OTP -> language menu -> action menu."""

import hmac
import re
from functools import wraps

from flask import Response, current_app, request
from plivo import plivoxml

from app.call_state import call_store
from app.prompts import (
    ACTION_PROMPTS,
    LANGUAGE_MENU,
    LANGUAGE_MENU_INVALID,
    OTP_PROMPTS,
    SPEAK_VOICES,
)
from app.routes import bp

OTP_PATTERN = re.compile(r"^[0-9]{4}$")
INPUT_TIMEOUT_SECONDS = 10
DIGIT_END_TIMEOUT_SECONDS = 5
DIAL_TIMEOUT_SECONDS = 30
LANGUAGE_BY_DIGIT = {"1": "en", "2": "es"}


def public_url(path):
    """Absolute URL for a webhook path, built from PUBLIC_BASE_URL."""
    base_url = current_app.config.get("PUBLIC_BASE_URL") or request.host_url
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def xml_response(element):
    return Response(element.to_string(False), mimetype="application/xml")


def redirect_to(response, path):
    response.add(plivoxml.RedirectElement(public_url(path), method="POST"))
    return response


def speak(text, language):
    return plivoxml.SpeakElement(text, **SPEAK_VOICES[language])


def dtmf_input(action_path, num_digits):
    return plivoxml.GetInputElement(
        action=public_url(action_path),
        method="POST",
        input_type="dtmf",
        num_digits=num_digits,
        execution_timeout=INPUT_TIMEOUT_SECONDS,
        digit_end_timeout=DIGIT_END_TIMEOUT_SECONDS,
    )


def dial_number(number):
    """Plivo's <Number>/callerId format: country code + number, digits only, no '+'."""
    return re.sub(r"\D", "", number or "")


def otp_matches(digits):
    """Constant-time comparison of caller input with the configured OTP."""
    if not OTP_PATTERN.match(digits):
        return False
    expected = current_app.config["BIRTHDATE_OTP"]
    return hmac.compare_digest(digits.encode(), expected.encode())


def requires_auth(view):
    """Menus are reachable only after a correct OTP on this call; otherwise restart at /answer."""

    @wraps(view)
    def wrapper():
        call_uuid = request.form.get("CallUUID")
        if not call_store.is_authenticated(call_uuid):
            current_app.logger.warning("Unauthenticated menu access for call %s", call_uuid)
            return xml_response(redirect_to(plivoxml.ResponseElement(), "/answer"))
        return view(call_uuid)

    return wrapper


def requires_language(view):
    """Level 2 also needs a Level 1 language choice; otherwise go back to Level 1."""

    @wraps(view)
    @requires_auth
    def wrapper(call_uuid):
        language = call_store.get_language(call_uuid)
        if language is None:
            return xml_response(redirect_to(plivoxml.ResponseElement(), "/menu/language"))
        return view(call_uuid, language)

    return wrapper


@bp.post("/answer")
def answer():
    response = plivoxml.ResponseElement()
    get_input = dtmf_input("/otp/verify", num_digits=4)
    get_input.add_speak(OTP_PROMPTS["welcome"])
    response.add(get_input)
    # Reached only when GetInput times out without input.
    response.add(plivoxml.SpeakElement(OTP_PROMPTS["no_input"]))
    return xml_response(redirect_to(response, "/answer"))


@bp.post("/otp/verify")
def verify_otp():
    call_uuid = request.form.get("CallUUID")
    digits = request.form.get("Digits", "")
    response = plivoxml.ResponseElement()

    # Log only the outcome and CallUUID, never the digits.
    if otp_matches(digits):
        current_app.logger.info("OTP attempt for call %s: correct", call_uuid)
        if call_uuid:
            call_store.mark_authenticated(call_uuid)
        response.add(plivoxml.SpeakElement(OTP_PROMPTS["verified"]))
        return xml_response(redirect_to(response, "/menu/language"))

    current_app.logger.info("OTP attempt for call %s: incorrect", call_uuid)
    response.add(plivoxml.SpeakElement(OTP_PROMPTS["incorrect"]))
    return xml_response(redirect_to(response, "/answer"))


@bp.post("/menu/language")
@requires_auth
def language_menu(call_uuid):
    response = plivoxml.ResponseElement()
    get_input = dtmf_input("/menu/language/select", num_digits=1)
    for language in ("en", "es"):
        get_input.add(speak(LANGUAGE_MENU[language], language))
    response.add(get_input)
    # Reached only when GetInput times out without input.
    return xml_response(redirect_to(response, "/menu/language"))


@bp.post("/menu/language/select")
@requires_auth
def select_language(call_uuid):
    language = LANGUAGE_BY_DIGIT.get(request.form.get("Digits", ""))
    response = plivoxml.ResponseElement()
    if language is None:
        response.add(speak(LANGUAGE_MENU_INVALID, "en"))
        return xml_response(redirect_to(response, "/menu/language"))

    call_store.set_language(call_uuid, language)
    current_app.logger.info("Call %s chose language %s", call_uuid, language)
    return xml_response(redirect_to(response, "/menu/action"))


@bp.post("/menu/action")
@requires_language
def action_menu(call_uuid, language):
    response = plivoxml.ResponseElement()
    get_input = dtmf_input("/menu/action/select", num_digits=1)
    get_input.add(speak(ACTION_PROMPTS[language]["menu"], language))
    response.add(get_input)
    # Reached only when GetInput times out without input.
    return xml_response(redirect_to(response, "/menu/action"))


@bp.post("/menu/action/select")
@requires_language
def select_action(call_uuid, language):
    digits = request.form.get("Digits", "")
    prompts = ACTION_PROMPTS[language]
    response = plivoxml.ResponseElement()

    if digits == "1":
        response.add(plivoxml.PlayElement(current_app.config["AUDIO_URL"]))
        return xml_response(redirect_to(response, "/menu/action"))

    if digits == "2":
        associate = dial_number(current_app.config.get("ASSOCIATE_NUMBER"))
        if associate:
            current_app.logger.info("Forwarding call %s to associate", call_uuid)
            response.add(speak(prompts["connecting"], language))
            dial = plivoxml.DialElement(
                caller_id=dial_number(current_app.config.get("PLIVO_FROM_NUMBER")) or None,
                timeout=DIAL_TIMEOUT_SECONDS,
            )
            dial.add(plivoxml.NumberElement(associate))
            response.add(dial)
        else:
            current_app.logger.error("ASSOCIATE_NUMBER is not configured; cannot forward call %s", call_uuid)
        # Runs after the dialled leg ends or fails to connect.
        response.add(speak(prompts["unavailable"], language))
        response.add(plivoxml.HangupElement())
        return xml_response(response)

    response.add(speak(prompts["invalid"], language))
    return xml_response(redirect_to(response, "/menu/action"))


@bp.post("/hangup")
def hangup():
    call_uuid = request.form.get("CallUUID")
    call_store.end_call(call_uuid)
    current_app.logger.info(
        "Call ended: uuid=%s status=%s cause=%s",
        call_uuid,
        request.form.get("CallStatus"),
        request.form.get("HangupCause"),
    )
    return "", 200
