from unittest.mock import MagicMock

import plivo
import pytest

from app import create_app
from app.call_state import authenticated_calls
from app.config import ENV_KEYS

TEST_CONFIG = {
    "TESTING": True,
    "PLIVO_AUTH_ID": "TEST_AUTH_ID",
    "PLIVO_AUTH_TOKEN": "test_auth_token",
    "PLIVO_FROM_NUMBER": "+910000000001",
    "ASSOCIATE_NUMBER": "+910000000002",
    "TARGET_NUMBER": "+910000000003",
    "PUBLIC_BASE_URL": "https://example.test",
}


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Ensure real credentials from the shell environment never leak into tests."""
    for key in ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture(autouse=True)
def clean_call_state():
    authenticated_calls.clear()
    yield
    authenticated_calls.clear()


@pytest.fixture(autouse=True)
def mock_plivo(monkeypatch):
    """Replace plivo.RestClient so no test can reach the real Plivo API.

    Returns the mocked RestClient class; the client instance is
    mock_plivo.return_value and calls.create returns request_uuid "test-request-uuid".
    """
    rest_client = MagicMock(name="RestClient")
    rest_client.return_value.calls.create.return_value = MagicMock(
        request_uuid="test-request-uuid"
    )
    monkeypatch.setattr(plivo, "RestClient", rest_client)
    return rest_client


@pytest.fixture
def app():
    return create_app(TEST_CONFIG)


@pytest.fixture
def client(app):
    return app.test_client()
