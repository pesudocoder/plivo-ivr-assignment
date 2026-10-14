import logging
import xml.etree.ElementTree as ET

import pytest

from app.call_state import call_store
from app.config import BIRTHDATE_OTP

BASE = "https://example.test"
CALL_A = "call-uuid-a"
CALL_B = "call-uuid-b"


def parse(response):
    assert response.status_code == 200
    assert response.mimetype == "application/xml"
    root = ET.fromstring(response.get_data())
    assert root.tag == "Response"
    return root


def wrong_otp(otp):
    """A well-formed 4-digit OTP guaranteed to differ from the real one."""
    return f"{(int(otp) + 1) % 10000:04d}"


def verify(client, digits, call_uuid=CALL_A):
    return client.post("/otp/verify", data={"CallUUID": call_uuid, "Digits": digits})


def assert_redirects_to(root, path):
    redirect = root[-1]
    assert redirect.tag == "Redirect"
    assert redirect.text == f"{BASE}{path}"
    assert redirect.get("method") == "POST"


def speak_texts(root):
    return [el.text for el in root.iter("Speak")]


@pytest.fixture
def otp(app):
    return app.config["BIRTHDATE_OTP"]


def test_r3_answer_prompts_for_4_digit_dtmf(client):
    root = parse(client.post("/answer"))

    get_input = root[0]
    assert get_input.tag == "GetInput"
    assert get_input.get("inputType") == "dtmf"
    assert get_input.get("numDigits") == "4"
    assert get_input.get("executionTimeout") == "10"
    assert get_input.get("action") == f"{BASE}/otp/verify"
    assert get_input.get("method") == "POST"
    prompt = get_input.find("Speak")
    assert prompt.text == "Welcome to the InspireWorks demo. Please enter your 4-digit OTP."


def test_r3_no_input_reprompts_via_redirect_to_answer(client):
    root = parse(client.post("/answer"))

    # Elements after GetInput run only when no input arrives before the timeout.
    after_input = list(root)[1:]
    assert [el.tag for el in after_input] == ["Speak", "Redirect"]
    assert after_input[0].text == "We did not receive any input."
    assert_redirects_to(root, "/answer")


def test_r3_redirect_urls_absolute_with_trailing_slash_base(app, client):
    app.config["PUBLIC_BASE_URL"] = f"{BASE}/"

    root = parse(client.post("/answer"))

    assert root[0].get("action") == f"{BASE}/otp/verify"
    assert_redirects_to(root, "/answer")


def test_r4_correct_otp_matches_birthdate_config(client, otp):
    assert otp == BIRTHDATE_OTP

    root = parse(verify(client, otp))

    assert speak_texts(root) == ["Thank you. You have been verified."]
    assert call_store.is_authenticated(CALL_A)


def test_r4_correct_otp_redirects_to_language_menu(client, otp):
    root = parse(verify(client, otp))

    assert_redirects_to(root, "/menu/language")


def test_r5_wrong_otp_reprompts(client, otp):
    root = parse(verify(client, wrong_otp(otp)))

    assert speak_texts(root) == ["Incorrect OTP. Please try again."]
    assert_redirects_to(root, "/answer")
    assert not call_store.is_authenticated(CALL_A)


def test_r5_repeated_wrong_otps_keep_reprompting(client, otp):
    for _ in range(5):
        root = parse(verify(client, wrong_otp(otp)))
        assert_redirects_to(root, "/answer")
        assert not call_store.is_authenticated(CALL_A)

    root = parse(verify(client, otp))

    assert_redirects_to(root, "/menu/language")
    assert call_store.is_authenticated(CALL_A)


@pytest.mark.parametrize(
    "make_digits",
    [
        pytest.param(lambda otp: "", id="empty"),
        pytest.param(lambda otp: otp[:3], id="short"),
        pytest.param(lambda otp: otp + "0", id="long"),
        pytest.param(lambda otp: otp[:3] + "#", id="nonnumeric"),
        pytest.param(lambda otp: "abcd", id="letters"),
        pytest.param(lambda otp: f" {otp}", id="padded"),
    ],
)
def test_r5_empty_short_long_and_nonnumeric_otp_rejected(client, otp, make_digits):
    root = parse(verify(client, make_digits(otp)))

    assert speak_texts(root) == ["Incorrect OTP. Please try again."]
    assert_redirects_to(root, "/answer")
    assert not call_store.is_authenticated(CALL_A)


def test_r5_missing_digits_param_rejected(client):
    root = parse(client.post("/otp/verify", data={"CallUUID": CALL_A}))

    assert_redirects_to(root, "/answer")
    assert not call_store.is_authenticated(CALL_A)


def test_r6_menu_without_auth_redirects_to_answer(client):
    root = parse(client.post("/menu/language", data={"CallUUID": CALL_A}))

    assert [el.tag for el in root] == ["Redirect"]
    assert_redirects_to(root, "/answer")


def test_r6_menu_without_call_uuid_redirects_to_answer(client):
    root = parse(client.post("/menu/language"))

    assert_redirects_to(root, "/answer")


def test_r6_menu_after_auth_allowed(client, otp):
    verify(client, otp)

    root = parse(client.post("/menu/language", data={"CallUUID": CALL_A}))

    assert [el.tag for el in root] == ["GetInput", "Redirect"]
    assert root[0].get("action") == f"{BASE}/menu/language/select"


def test_r6_auth_is_per_call(client, otp):
    verify(client, otp, call_uuid=CALL_A)

    root = parse(client.post("/menu/language", data={"CallUUID": CALL_B}))

    assert not call_store.is_authenticated(CALL_B)
    assert_redirects_to(root, "/answer")


def test_r6_hangup_clears_auth(client, otp):
    verify(client, otp)
    assert call_store.is_authenticated(CALL_A)

    client.post("/hangup", data={"CallUUID": CALL_A, "CallStatus": "completed"})

    assert not call_store.is_authenticated(CALL_A)
    root = parse(client.post("/menu/language", data={"CallUUID": CALL_A}))
    assert_redirects_to(root, "/answer")


def test_otp_value_never_in_xml_or_logs(client, otp, caplog):
    with caplog.at_level(logging.DEBUG):
        responses = [
            client.post("/answer"),
            verify(client, wrong_otp(otp)),
            verify(client, otp),
            client.post("/menu/language", data={"CallUUID": CALL_A}),
            client.post("/hangup", data={"CallUUID": CALL_A}),
        ]

    for response in responses:
        assert otp not in response.get_data(as_text=True)
    assert otp not in caplog.text
    assert wrong_otp(otp) not in caplog.text
    assert "correct" in caplog.text and "incorrect" in caplog.text
