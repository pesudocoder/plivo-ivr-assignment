import logging
import xml.etree.ElementTree as ET

import pytest

from app.call_state import call_store
from app.prompts import ACTION_PROMPTS, SPEAK_VOICES

BASE = "https://example.test"
CALL_A = "call-uuid-a"
LANGUAGE_DIGIT = {"en": "1", "es": "2"}
FAILED_STATUSES = ["busy", "failed", "timeout", "no-answer", "cancel", "", None]


def parse(response):
    assert response.status_code == 200
    assert response.mimetype == "application/xml"
    root = ET.fromstring(response.get_data())
    assert root.tag == "Response"
    return root


@pytest.fixture(params=["en", "es"])
def language(request, client, app):
    """CALL_A is authenticated and has chosen the parametrized language."""
    client.post("/otp/verify", data={"CallUUID": CALL_A, "Digits": app.config["BIRTHDATE_OTP"]})
    client.post("/menu/language/select", data={"CallUUID": CALL_A, "Digits": LANGUAGE_DIGIT[request.param]})
    assert call_store.get_language(CALL_A) == request.param
    return request.param


def dial_status(client, status):
    data = {"CallUUID": CALL_A}
    if status is not None:
        data["DialStatus"] = status
    return parse(client.post("/menu/dial/status", data=data))


def assert_spoken_then_hangup(root, text, language):
    assert [el.tag for el in root] == ["Speak", "Hangup"]
    assert root[0].text == text
    assert root[0].get("language") == SPEAK_VOICES[language]["language"]


def test_r9_dial_has_status_action_url(client, language):
    root = parse(client.post("/menu/action/select", data={"CallUUID": CALL_A, "Digits": "2"}))

    dial = root.find("Dial")
    assert dial.get("action") == f"{BASE}/menu/dial/status"
    assert dial.get("method") == "POST"
    # No unconditional "unavailable" message after Dial anymore.
    assert root[-1].tag == "Dial"
    assert ACTION_PROMPTS[language]["unavailable"] not in [el.text for el in root.iter("Speak")]


def test_r9_dial_completed_says_goodbye_not_unavailable(client, language):
    root = dial_status(client, "completed")

    assert_spoken_then_hangup(root, ACTION_PROMPTS[language]["goodbye"], language)


@pytest.mark.parametrize("status", FAILED_STATUSES, ids=lambda s: "missing" if s is None else (s or "empty"))
def test_r9_dial_failed_statuses_say_unavailable(client, language, status):
    root = dial_status(client, status)

    assert_spoken_then_hangup(root, ACTION_PROMPTS[language]["unavailable"], language)


def test_r9_dial_status_logged_with_call_uuid(client, language, caplog):
    with caplog.at_level(logging.INFO):
        dial_status(client, "busy")

    assert CALL_A in caplog.text and "DialStatus=busy" in caplog.text


def test_r9_dial_status_unauthenticated_redirects_to_answer(client):
    root = dial_status(client, "completed")

    assert [el.tag for el in root] == ["Redirect"]
    assert root[0].text == f"{BASE}/answer"
