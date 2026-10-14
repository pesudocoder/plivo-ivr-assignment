"""Restrict the call trigger (GET / and POST /call) to the local machine.

The Flask server is exposed through ngrok so Plivo can reach the XML webhooks,
which means every route is reachable from the internet. Anyone who found the
ngrok URL could otherwise place calls billed to our Plivo account. So:

- ngrok forwards requests from the local agent, so remote_addr is loopback even
  for internet traffic; ngrok adds X-Forwarded-For, so any request carrying it
  is treated as tunnelled and rejected.
- Requests from other hosts (e.g. the LAN, since run.py binds 0.0.0.0) have a
  non-loopback remote_addr and are rejected.
- A cross-site page in the local browser could POST to http://127.0.0.1:5000;
  browsers send an Origin header on such requests, so a mismatched Origin is
  rejected too. CLI tools (curl, scripts) send no Origin and are unaffected.

The Plivo webhooks (/answer, /otp/verify, /menu/..., /hangup) do NOT use this
guard; they must stay publicly reachable for Plivo.
"""

import ipaddress
from functools import wraps
from urllib.parse import urlsplit

from flask import jsonify, request

FORBIDDEN_MESSAGE = "Forbidden: the call trigger is only available from this machine (http://127.0.0.1:5000)."


def is_local_request():
    if "X-Forwarded-For" in request.headers:
        return False
    try:
        if not ipaddress.ip_address(request.remote_addr or "").is_loopback:
            return False
    except ValueError:
        return False
    origin = request.headers.get("Origin")
    if origin is not None and urlsplit(origin).netloc != request.host:
        return False
    return True


def local_only(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not is_local_request():
            return jsonify(status="error", error=FORBIDDEN_MESSAGE), 403
        return view(*args, **kwargs)

    return wrapper
