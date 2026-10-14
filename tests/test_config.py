import pytest

from app import create_app
from app.config import (
    BIRTHDATE_OTP,
    MissingCredentialsError,
    load_config,
    require_call_config,
)


def test_load_config_reads_env_vars(monkeypatch):
    monkeypatch.setenv("PLIVO_AUTH_ID", "ENV_ID")
    monkeypatch.setenv("PLIVO_AUTH_TOKEN", "env_token")
    monkeypatch.setenv("PLIVO_FROM_NUMBER", "+911111111111")
    monkeypatch.setenv("ASSOCIATE_NUMBER", "+912222222222")
    monkeypatch.setenv("TARGET_NUMBER", "+913333333333")
    monkeypatch.setenv("PUBLIC_BASE_URL", "https://env.example")

    config = load_config()

    assert config["PLIVO_AUTH_ID"] == "ENV_ID"
    assert config["PLIVO_AUTH_TOKEN"] == "env_token"
    assert config["PLIVO_FROM_NUMBER"] == "+911111111111"
    assert config["ASSOCIATE_NUMBER"] == "+912222222222"
    assert config["TARGET_NUMBER"] == "+913333333333"
    assert config["PUBLIC_BASE_URL"] == "https://env.example"


def test_birthdate_otp_is_four_digit_ddmm():
    assert len(BIRTHDATE_OTP) == 4 and BIRTHDATE_OTP.isdigit()
    day, month = int(BIRTHDATE_OTP[:2]), int(BIRTHDATE_OTP[2:])
    assert 1 <= day <= 31 and 1 <= month <= 12
    assert load_config({})["BIRTHDATE_OTP"] == BIRTHDATE_OTP


def test_app_boots_without_credentials():
    app = create_app()

    assert app.config["PLIVO_AUTH_ID"] is None
    assert app.test_client().get("/health").status_code == 200


def test_missing_credentials_raises_clear_error():
    config = load_config({"PLIVO_AUTH_ID": "ID_ONLY"})

    with pytest.raises(MissingCredentialsError) as exc_info:
        require_call_config(config)

    message = str(exc_info.value)
    assert "PLIVO_AUTH_TOKEN" in message
    assert "PLIVO_FROM_NUMBER" in message
    assert "PUBLIC_BASE_URL" in message
    assert "PLIVO_AUTH_ID" not in message


def test_empty_string_credentials_count_as_missing():
    config = load_config({"PLIVO_AUTH_ID": "", "PLIVO_AUTH_TOKEN": ""})

    with pytest.raises(MissingCredentialsError) as exc_info:
        require_call_config(config)

    assert "PLIVO_AUTH_ID" in exc_info.value.missing


def test_complete_config_passes_call_check(app):
    require_call_config(app.config)
