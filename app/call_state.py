"""Per-call IVR state: OTP authentication and chosen language.

Demo-grade: in-memory structures guarded by a lock. They live in a single
process and are lost on restart, which is fine for this assignment (no
database). A multi-worker or production deployment would need a shared store
such as Redis.
"""

import threading


class CallStore:
    """Thread-safe per-CallUUID state, cleared when the call hangs up."""

    def __init__(self):
        self._lock = threading.Lock()
        self._authenticated = set()
        self._languages = {}

    def mark_authenticated(self, call_uuid):
        with self._lock:
            self._authenticated.add(call_uuid)

    def is_authenticated(self, call_uuid):
        with self._lock:
            return call_uuid in self._authenticated

    def set_language(self, call_uuid, language):
        with self._lock:
            self._languages[call_uuid] = language

    def get_language(self, call_uuid):
        with self._lock:
            return self._languages.get(call_uuid)

    def end_call(self, call_uuid):
        with self._lock:
            self._authenticated.discard(call_uuid)
            self._languages.pop(call_uuid, None)

    def clear(self):
        with self._lock:
            self._authenticated.clear()
            self._languages.clear()


call_store = CallStore()
