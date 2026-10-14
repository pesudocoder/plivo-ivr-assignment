import logging
import xml.etree.ElementTree as ET

import pytest

from app.call_state import call_store
from app.config import DEFAULT_AUDIO_URL
from app.prompts import (
    ACTION_PROMPTS,
    LANGUAGE_MENU,
    LANGUAGE_MENU_INVALID,
    OTP_PROMPTS,
    SPEAK_VOICES,
)
from tests.conftest import TEST_CONFIG

BASE = "https://example.test"
CALL_A = "call-uuid-a"
CALL_B = "call-uuid-b"
MENU_ROUTES = ["/menu/language", "/menu/language/select", "/menu/action", "/menu/action/select"]


def parse(response):
    assert response.status_code == 200
    assert response.mimetype == "application/xml"
    root = ET.fromstring(response.get_data())
    assert root.tag == "Response"
    return root


def post(client, path, call_uuid=CALL_A, digits=None):
    data = {"CallUUID": call_uuid}
    if digits is not None:
        data["Digits"] = digits
    return parse(client.post(path, data=data))


def redirect_target(root):
    redirect = root[-1]
    assert redirect.tag == "Redirect"
    assert redirect.get("method") == "POST"
    return redirect.text.removeprefix(BASE)


def assert_speak(element, text, language):
    assert element.tag == "Speak"
    assert element.text == text
    assert element.get("language") == SPEAK_VOICES[language]["language"]


def wrong_otp(otp):
    return f"{(int(otp) + 1) % 10000:04d}"


@pytest.fixture
def otp(app):
    return app.config["BIRTHDATE_OTP"]


@pytest.fixture
def authed(client, otp):
    """CALL_A has entered the correct OTP."""
    post(client, "/otp/verify", digits=otp)
    assert call_store.is_authenticated(CALL_A)


@pytest.fixture
def english(client, authed):
    post(client, "/menu/language/select", digits="1")


@pytest.fixture
def spanish(client, authed):
    post(client, "/menu/language/select", digits="2")


# --- R7: Level 1 language menu ---


def test_r7_language_menu_offers_english_1_and_spanish_2(client, authed):
    root = post(client, "/menu/language")

    get_input = root[0]
    assert get_input.tag == "GetInput"
    assert get_input.get("action") == f"{BASE}/menu/language/select"
    speaks = list(get_input)
    assert len(speaks) == 2
    assert_speak(speaks[0], LANGUAGE_MENU["en"], "en")
    assert_speak(speaks[1], LANGUAGE_MENU["es"], "es")
    assert "press 1" in speaks[0].text and "presione 2" in speaks[1].text


def test_r7_press_1_selects_english(client, authed):
    root = post(client, "/menu/language/select", digits="1")

    assert call_store.get_language(CALL_A) == "en"
    assert redirect_target(root) == "/menu/action"


def test_r7_press_2_selects_spanish(client, authed):
    root = post(client, "/menu/language/select", digits="2")

    assert call_store.get_language(CALL_A) == "es"
    assert redirect_target(root) == "/menu/action"


# --- R8 / R9: Level 2 actions ---


def test_r8_action_1_plays_public_mp3(app, client, english):
    root = post(client, "/menu/action/select", digits="1")

    assert [el.tag for el in root] == ["Play", "Redirect"]
    assert root[0].text == app.config["AUDIO_URL"] == DEFAULT_AUDIO_URL
    assert root[0].text.startswith("https://")
    assert redirect_target(root) == "/menu/action"


def test_r8_audio_url_overridable(app, client, english):
    app.config["AUDIO_URL"] = "https://cdn.example.test/custom.mp3"

    root = post(client, "/menu/action/select", digits="1")

    assert root[0].text == "https://cdn.example.test/custom.mp3"


def test_r9_action_2_dials_associate_number(client, english):
    root = post(client, "/menu/action/select", digits="2")

    assert [el.tag for el in root] == ["Speak", "Dial", "Speak", "Hangup"]
    assert_speak(root[0], ACTION_PROMPTS["en"]["connecting"], "en")
    dial = root[1]
    # Plivo's documented Dial format: country code + number, no leading '+'.
    assert dial.get("callerId") == TEST_CONFIG["PLIVO_FROM_NUMBER"].lstrip("+")
    numbers = dial.findall("Number")
    assert len(numbers) == 1
    assert numbers[0].text == TEST_CONFIG["ASSOCIATE_NUMBER"].lstrip("+")
    assert_speak(root[2], ACTION_PROMPTS["en"]["unavailable"], "en")


def test_r9_associate_number_normalized(app, client, english):
    app.config["ASSOCIATE_NUMBER"] = "+91 22-6423 6412"

    root = post(client, "/menu/action/select", digits="2")

    assert root.find("Dial/Number").text == "912264236412"


def test_r9_missing_associate_number_speaks_unavailable(app, client, english):
    app.config["ASSOCIATE_NUMBER"] = None

    root = post(client, "/menu/action/select", digits="2")

    assert [el.tag for el in root] == ["Speak", "Hangup"]
    assert_speak(root[0], ACTION_PROMPTS["en"]["unavailable"], "en")


# --- R10: Level 2 language ---


def test_r10_level2_prompts_in_english(client, english):
    root = post(client, "/menu/action")

    get_input = root[0]
    assert get_input.tag == "GetInput"
    assert get_input.get("action") == f"{BASE}/menu/action/select"
    assert_speak(get_input.find("Speak"), ACTION_PROMPTS["en"]["menu"], "en")


def test_r10_level2_prompts_in_spanish(client, spanish):
    root = post(client, "/menu/action")

    prompt = root[0].find("Speak")
    assert_speak(prompt, ACTION_PROMPTS["es"]["menu"], "es")
    assert prompt.get("language").startswith("es-")

    forward = post(client, "/menu/action/select", digits="2")
    assert_speak(forward[0], ACTION_PROMPTS["es"]["connecting"], "es")
    assert_speak(forward[2], ACTION_PROMPTS["es"]["unavailable"], "es")


def test_r10_language_is_per_call(client, otp):
    post(client, "/otp/verify", call_uuid=CALL_A, digits=otp)
    post(client, "/otp/verify", call_uuid=CALL_B, digits=otp)
    post(client, "/menu/language/select", call_uuid=CALL_A, digits="1")
    post(client, "/menu/language/select", call_uuid=CALL_B, digits="2")

    root_a = post(client, "/menu/action", call_uuid=CALL_A)
    root_b = post(client, "/menu/action", call_uuid=CALL_B)

    assert_speak(root_a[0].find("Speak"), ACTION_PROMPTS["en"]["menu"], "en")
    assert_speak(root_b[0].find("Speak"), ACTION_PROMPTS["es"]["menu"], "es")


# --- R11 / R12: Plivo XML and DTMF ---


def test_r11_all_menu_responses_are_valid_plivo_xml(client, english):
    paths_and_digits = [
        ("/answer", None),
        ("/menu/language", None),
        ("/menu/language/select", "1"),
        ("/menu/language/select", "9"),
        ("/menu/action", None),
        ("/menu/action/select", "1"),
        ("/menu/action/select", "2"),
        ("/menu/action/select", "9"),
    ]
    allowed = {"GetInput", "Speak", "Play", "Dial", "Number", "Redirect", "Hangup"}
    for path, digits in paths_and_digits:
        root = post(client, path, digits=digits)
        assert len(root) > 0, path
        assert {el.tag for el in root.iter()} - {"Response"} <= allowed, path
        for redirect in root.iter("Redirect"):
            assert redirect.text.startswith(f"{BASE}/"), path
        for get_input in root.iter("GetInput"):
            assert get_input.get("action").startswith(f"{BASE}/"), path


def test_r12_dtmf_handled_at_every_level(client, english):
    levels = {
        "/answer": ("4", "/otp/verify"),
        "/menu/language": ("1", "/menu/language/select"),
        "/menu/action": ("1", "/menu/action/select"),
    }
    for path, (num_digits, action) in levels.items():
        get_input = post(client, path)[0]
        assert get_input.tag == "GetInput", path
        assert get_input.get("inputType") == "dtmf", path
        assert get_input.get("numDigits") == num_digits, path
        assert get_input.get("action") == f"{BASE}{action}", path
        assert get_input.get("method") == "POST", path


# --- R13: branching across the whole call ---


def test_r13_full_flow_english_audio_then_forward(app, client, otp):
    root = post(client, "/answer")
    assert redirect_target(root) == "/answer"

    root = post(client, "/otp/verify", digits=wrong_otp(otp))
    assert root[0].text == OTP_PROMPTS["incorrect"]
    assert redirect_target(root) == "/answer"
    assert redirect_target(post(client, "/menu/language")) == "/answer"

    root = post(client, "/otp/verify", digits=otp)
    assert redirect_target(root) == "/menu/language"

    post(client, "/menu/language")
    root = post(client, "/menu/language/select", digits="1")
    assert redirect_target(root) == "/menu/action"

    post(client, "/menu/action")
    root = post(client, "/menu/action/select", digits="1")
    assert root.find("Play").text == app.config["AUDIO_URL"]
    assert redirect_target(root) == "/menu/action"

    post(client, "/menu/action")
    root = post(client, "/menu/action/select", digits="2")
    assert root.find("Dial/Number").text == TEST_CONFIG["ASSOCIATE_NUMBER"].lstrip("+")
    assert root[-1].tag == "Hangup"

    client.post("/hangup", data={"CallUUID": CALL_A, "CallStatus": "completed"})
    assert not call_store.is_authenticated(CALL_A)


def test_r13_full_flow_spanish(app, client, otp):
    post(client, "/answer")
    assert redirect_target(post(client, "/otp/verify", digits=otp)) == "/menu/language"
    assert redirect_target(post(client, "/menu/language/select", digits="2")) == "/menu/action"

    root = post(client, "/menu/action")
    assert_speak(root[0].find("Speak"), ACTION_PROMPTS["es"]["menu"], "es")

    root = post(client, "/menu/action/select", digits="1")
    assert root.find("Play").text == app.config["AUDIO_URL"]

    root = post(client, "/menu/action/select", digits="2")
    assert_speak(root[0], ACTION_PROMPTS["es"]["connecting"], "es")
    assert root.find("Dial") is not None


# --- R14: invalid input and timeouts ---


@pytest.mark.parametrize("digits", ["0", "3", "9", "*", "#", "", "12"])
def test_r14_invalid_language_key_repeats_level1(client, authed, digits):
    root = post(client, "/menu/language/select", digits=digits)

    assert [el.tag for el in root] == ["Speak", "Redirect"]
    assert root[0].text == LANGUAGE_MENU_INVALID
    assert redirect_target(root) == "/menu/language"
    assert call_store.get_language(CALL_A) is None


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("digits", ["0", "3", "9", "*", "#", ""])
def test_r14_invalid_action_key_repeats_level2_in_chosen_language(client, authed, language, digits):
    post(client, "/menu/language/select", digits={"en": "1", "es": "2"}[language])

    root = post(client, "/menu/action/select", digits=digits)

    assert [el.tag for el in root] == ["Speak", "Redirect"]
    assert_speak(root[0], ACTION_PROMPTS[language]["invalid"], language)
    assert redirect_target(root) == "/menu/action"


def test_r14_no_input_repeats_each_level(client, english):
    # Elements after GetInput run only when the caller enters nothing before the timeout.
    for path in ["/answer", "/menu/language", "/menu/action"]:
        root = post(client, path)
        assert root[0].tag == "GetInput", path
        assert redirect_target(root) == path, path


# --- R6 gating, language gating, hangup ---


@pytest.mark.parametrize("path", MENU_ROUTES)
def test_r6_menus_reject_unauthenticated_calls(client, path, caplog):
    with caplog.at_level(logging.WARNING):
        root = post(client, path, digits="1")

    assert [el.tag for el in root] == ["Redirect"]
    assert redirect_target(root) == "/answer"
    assert call_store.get_language(CALL_A) is None


@pytest.mark.parametrize("path", ["/menu/action", "/menu/action/select"])
def test_action_menu_without_language_redirects_to_language_menu(client, authed, path):
    root = post(client, path, digits="1")

    assert [el.tag for el in root] == ["Redirect"]
    assert redirect_target(root) == "/menu/language"


def test_hangup_clears_language(client, english):
    assert call_store.get_language(CALL_A) == "en"

    client.post("/hangup", data={"CallUUID": CALL_A, "CallStatus": "completed"})

    assert call_store.get_language(CALL_A) is None
    assert redirect_target(post(client, "/menu/action")) == "/answer"


def test_otp_never_exposed_through_menus(client, english, otp, caplog):
    with caplog.at_level(logging.DEBUG):
        bodies = [
            client.post(path, data={"CallUUID": CALL_A, "Digits": digits}).get_data(as_text=True)
            for path, digits in [
                ("/menu/language", ""),
                ("/menu/action", ""),
                ("/menu/action/select", "1"),
                ("/menu/action/select", "2"),
            ]
        ]

    assert all(otp not in body for body in bodies)
    assert otp not in caplog.text
