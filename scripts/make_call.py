"""Trigger an outbound IVR call from the command line.

Usage: python scripts/make_call.py [--to +91XXXXXXXXXX]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import MissingCredentialsError, load_config  # noqa: E402
from app.plivo_client import (  # noqa: E402
    InvalidNumberError,
    PlivoCallError,
    make_outbound_call,
)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Place an outbound Plivo IVR call.")
    parser.add_argument("--to", help="Target number in E.164 format (defaults to TARGET_NUMBER)")
    args = parser.parse_args(argv)

    try:
        request_uuid = make_outbound_call(load_config(), to_number=args.to)
    except (MissingCredentialsError, InvalidNumberError, PlivoCallError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Call initiated. request_uuid: {request_uuid}")
    return 0


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    sys.exit(main())
