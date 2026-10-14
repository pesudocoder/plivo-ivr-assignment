"""Plivo XML webhooks for the IVR call flow: OTP -> language menu -> action menu."""

import hmac
import re

from flask import Response, current_app, request
from plivo import plivoxml

from app.call_state import authenticated_calls
from app.routes import bp

OTP_PATTERN = re.compile(r"^[0-9]{4}$")
INPUT_TIMEOUT_SECONDS = 10
DIGIT_END_TIMEOUT_SECONDS = 5


def public_url(path):
    """Absolute URL for a webhook path, built from PUBLIC_BASE_URL."""
    base_url = current_app.config.get("PUBLIC_BASE_URL") or request.host_url
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def xml_response(element):
    return Response(element.to_string(False), mimetype="application/xml")


def redirect_to(response, path):
    response.add(plivoxml.RedirectElement(public_url(path), method="POST"))
    return response


def otp_matches(digits):
    """Constant-time comparison of caller input with the configured OTP."""
    if not OTP_PATTERN.match(digits):
        return False
    expected = current_app.config["BIRTHDATE_OTP"]
    return hmac.compare_digest(digits.encode(), expected.encode())


@bp.post("/answer")
def answer():
    response = plivoxml.ResponseElement()
    get_input = plivoxml.GetInputElement(
        action=public_url("/otp/verify"),
        method="POST",
        input_type="dtmf",
        num_digits=4,
        execution_timeout=INPUT_TIMEOUT_SECONDS,
        digit_end_timeout=DIGIT_END_TIMEOUT_SECONDS,
    )
    get_input.add_speak("Welcome to the InspireWorks demo. Please enter your 4-digit OTP.")
    response.add(get_input)
    # Reached only when GetInput times out without input.
    response.add(plivoxml.SpeakElement("We did not receive any input."))
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
            authenticated_calls.add(call_uuid)
        response.add(plivoxml.SpeakElement("Thank you. You have been verified."))
        return xml_response(redirect_to(response, "/menu/language"))

    current_app.logger.info("OTP attempt for call %s: incorrect", call_uuid)
    response.add(plivoxml.SpeakElement("Incorrect OTP. Please try again."))
    return xml_response(redirect_to(response, "/answer"))


@bp.post("/menu/language")
def language_menu():
    # TEMPORARY placeholder for Phase 3; Phase 4 replaces this with the Level 1 menu.
    response = plivoxml.ResponseElement()
    if request.form.get("CallUUID") not in authenticated_calls:
        return xml_response(redirect_to(response, "/answer"))

    response.add(
        plivoxml.SpeakElement(
            "Authentication complete. The menu will be added in the next phase."
        )
    )
    response.add(plivoxml.HangupElement())
    return xml_response(response)


@bp.post("/hangup")
def hangup():
    call_uuid = request.form.get("CallUUID")
    authenticated_calls.discard(call_uuid)
    current_app.logger.info(
        "Call ended: uuid=%s status=%s cause=%s",
        call_uuid,
        request.form.get("CallStatus"),
        request.form.get("HangupCause"),
    )
    return "", 200
