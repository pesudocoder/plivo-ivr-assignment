import pytest

from app import create_app
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


@pytest.fixture
def app():
    return create_app(TEST_CONFIG)


@pytest.fixture
def client(app):
    return app.test_client()
