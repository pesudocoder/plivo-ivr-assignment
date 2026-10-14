"""Per-call authentication state.

Demo-grade: an in-memory set guarded by a lock. It lives in a single process
and is lost on restart, which is fine for this assignment (no database). A
multi-worker or production deployment would need a shared store such as Redis.
"""

import threading


class AuthenticatedCalls:
    """Thread-safe set of CallUUIDs that have entered the correct OTP."""

    def __init__(self):
        self._lock = threading.Lock()
        self._call_uuids = set()

    def add(self, call_uuid):
        with self._lock:
            self._call_uuids.add(call_uuid)

    def discard(self, call_uuid):
        with self._lock:
            self._call_uuids.discard(call_uuid)

    def __contains__(self, call_uuid):
        with self._lock:
            return call_uuid in self._call_uuids

    def clear(self):
        with self._lock:
            self._call_uuids.clear()


authenticated_calls = AuthenticatedCalls()
