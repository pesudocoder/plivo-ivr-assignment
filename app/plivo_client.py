"""Outbound calls through the Plivo REST API."""

import logging
import re

import plivo
import requests

from app.config import MissingCredentialsError, require_call_config

logger = logging.getLogger(__name__)

E164_PATTERN = re.compile(r"^\+\d{8,15}$")


class InvalidNumberError(ValueError):
    """Raised when the target number is not in E.164 format."""


class PlivoCallError(RuntimeError):
    """Raised when the Plivo API rejects or fails the call request."""


def _redact(text, secret):
    return text.replace(secret, "[REDACTED]") if secret else text


def make_outbound_call(config, to_number=None):
    """Place an outbound call from PLIVO_FROM_NUMBER and return Plivo's request_uuid."""
    require_call_config(config)

    target = to_number or config.get("TARGET_NUMBER")
    if not target:
        raise MissingCredentialsError(["TARGET_NUMBER"])
    if not isinstance(target, str) or not E164_PATTERN.match(target):
        raise InvalidNumberError(
            f"Invalid target number {target!r}: expected E.164 format, "
            "'+' followed by 8-15 digits (e.g. +919876543210)."
        )

    base_url = config["PUBLIC_BASE_URL"].rstrip("/")
    auth_token = config["PLIVO_AUTH_TOKEN"]
    try:
        client = plivo.RestClient(config["PLIVO_AUTH_ID"], auth_token)
        response = client.calls.create(
            from_=config["PLIVO_FROM_NUMBER"],
            to_=target,
            answer_url=f"{base_url}/answer",
            answer_method="POST",
            hangup_url=f"{base_url}/hangup",
            hangup_method="POST",
        )
    except (plivo.exceptions.PlivoRestError, requests.exceptions.RequestException) as exc:
        message = _redact(f"Plivo API call failed ({type(exc).__name__}): {exc}", auth_token)
        logger.error(message)
        raise PlivoCallError(message) from None

    request_uuid = response.request_uuid
    logger.info("Outbound call initiated to %s, request_uuid=%s", target, request_uuid)
    return request_uuid
