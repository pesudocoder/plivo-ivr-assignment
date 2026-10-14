"""Application configuration loaded from environment variables.

Values come from the process environment. run.py calls python-dotenv's
load_dotenv() so a local .env file populates the environment in development;
tests never load .env and supply their own config instead.
"""

import os

# Hardcoded OTP: birthdate in DDMM format. Placeholder - replace with the real value.
BIRTHDATE_OTP = "2707"

ENV_KEYS = (
    "PLIVO_AUTH_ID",
    "PLIVO_AUTH_TOKEN",
    "PLIVO_FROM_NUMBER",
    "ASSOCIATE_NUMBER",
    "TARGET_NUMBER",
    "PUBLIC_BASE_URL",
    "AUDIO_URL",
)

# Publicly hosted MP3 played at Level 2 option 1 (Plivo's sample file) unless AUDIO_URL is set.
DEFAULT_AUDIO_URL = "https://s3.amazonaws.com/plivocloud/music.mp3"

# Settings that must be present before an outbound call can be placed.
REQUIRED_FOR_CALL = (
    "PLIVO_AUTH_ID",
    "PLIVO_AUTH_TOKEN",
    "PLIVO_FROM_NUMBER",
    "PUBLIC_BASE_URL",
)


class MissingCredentialsError(RuntimeError):
    """Raised when a call is attempted without the required Plivo settings."""

    def __init__(self, missing):
        self.missing = list(missing)
        super().__init__(
            "Cannot place call: missing required configuration "
            f"{', '.join(self.missing)}. Set them in .env (see .env.example)."
        )


def load_config(environ=None):
    """Build a config dict from the environment. Missing values become None."""
    environ = os.environ if environ is None else environ
    config = {key: (environ.get(key) or None) for key in ENV_KEYS}
    config["AUDIO_URL"] = config["AUDIO_URL"] or DEFAULT_AUDIO_URL
    config["BIRTHDATE_OTP"] = BIRTHDATE_OTP
    return config


def require_call_config(config):
    """Raise MissingCredentialsError unless every setting needed for a call is set."""
    missing = [key for key in REQUIRED_FOR_CALL if not config.get(key)]
    if missing:
        raise MissingCredentialsError(missing)
