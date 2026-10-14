import logging

import plivo
import pytest

from tests.conftest import TEST_CONFIG


def create_kwargs(mock_plivo):
    mock_plivo.return_value.calls.create.assert_called_once()
    return mock_plivo.return_value.calls.create.call_args.kwargs


def test_r1_call_uses_plivo_from_number_and_target(client, mock_plivo):
    response = client.post("/call")

    assert response.status_code == 200
    mock_plivo.assert_called_once_with(
        TEST_CONFIG["PLIVO_AUTH_ID"], TEST_CONFIG["PLIVO_AUTH_TOKEN"]
    )
    kwargs = create_kwargs(mock_plivo)
    assert kwargs["from_"] == TEST_CONFIG["PLIVO_FROM_NUMBER"]
    assert kwargs["to_"] == TEST_CONFIG["TARGET_NUMBER"]


def test_r1_answer_and_hangup_urls_built_from_public_base_url(client, mock_plivo):
    client.post("/call")

    kwargs = create_kwargs(mock_plivo)
    assert kwargs["answer_url"] == "https://example.test/answer"
    assert kwargs["answer_method"] == "POST"
    assert kwargs["hangup_url"] == "https://example.test/hangup"
    assert kwargs["hangup_method"] == "POST"


def test_r1_base_url_trailing_slash_not_doubled(app, client, mock_plivo):
    app.config["PUBLIC_BASE_URL"] = "https://example.test/"

    client.post("/call")

    assert create_kwargs(mock_plivo)["answer_url"] == "https://example.test/answer"


def test_r1_returns_request_uuid(client):
    response = client.post("/call")

    assert response.get_json() == {"status": "initiated", "request_uuid": "test-request-uuid"}


def test_r2_target_defaults_to_config_target_number(client, mock_plivo):
    client.post("/call", json={})

    assert create_kwargs(mock_plivo)["to_"] == TEST_CONFIG["TARGET_NUMBER"]


def test_r2_target_overridable_via_request_body(client, mock_plivo):
    response = client.post("/call", json={"to": "+919999999999"})

    assert response.status_code == 200
    assert create_kwargs(mock_plivo)["to_"] == "+919999999999"


@pytest.mark.parametrize(
    "number",
    ["9999999999", "+91-99999-99999", "+1234567", "+1234567890123456", "+91abc9999999", 919999999999],
)
def test_r2_invalid_number_rejected_400(client, mock_plivo, number):
    response = client.post("/call", json={"to": number})

    assert response.status_code == 400
    assert "E.164" in response.get_json()["error"]
    mock_plivo.return_value.calls.create.assert_not_called()


def test_r2_non_object_body_rejected_400(client, mock_plivo):
    response = client.post("/call", json=["+919999999999"])

    assert response.status_code == 400
    mock_plivo.return_value.calls.create.assert_not_called()


def test_call_missing_config_returns_500(app, client, mock_plivo):
    app.config["PLIVO_AUTH_TOKEN"] = None

    response = client.post("/call")

    assert response.status_code == 500
    assert "PLIVO_AUTH_TOKEN" in response.get_json()["error"]
    mock_plivo.assert_not_called()


def test_call_missing_target_number_returns_500(app, client, mock_plivo):
    app.config["TARGET_NUMBER"] = None

    response = client.post("/call")

    assert response.status_code == 500
    assert "TARGET_NUMBER" in response.get_json()["error"]
    mock_plivo.return_value.calls.create.assert_not_called()


def test_call_plivo_api_error_returns_502_without_leaking_token(client, mock_plivo, caplog):
    token = TEST_CONFIG["PLIVO_AUTH_TOKEN"]
    mock_plivo.return_value.calls.create.side_effect = plivo.exceptions.AuthenticationError(
        f"Authentication failed for token {token}"
    )

    with caplog.at_level(logging.DEBUG):
        response = client.post("/call")

    assert response.status_code == 502
    body = response.get_data(as_text=True)
    assert "AuthenticationError" in body
    assert token not in body
    assert token not in caplog.text
