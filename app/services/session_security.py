from __future__ import annotations

import time
from collections import deque

from app.core.config import settings
from app.services.state_store import state_store


class SessionSecurityStore:
    def __init__(self) -> None:
        self.injection_prefix = "session_injection_attempts:"
        self.quarantine_prefix = "session_quarantine:"

    def _load_attempts(self, session_id: str) -> deque[float]:
        raw = state_store.get_json_list(f"{self.injection_prefix}{session_id}")
        values = [float(x) for x in raw if isinstance(x, (int, float))]
        return deque(values)

    def _save_attempts(self, session_id: str, attempts: deque[float]) -> None:
        key = f"{self.injection_prefix}{session_id}"
        bounded = list(attempts)[-settings.prompt_injection_max_attempts:]
        state_store.set_json_list(key=key, values=bounded, ttl_seconds=settings.prompt_injection_window_seconds)

    def _evict_old_attempts(self, session_id: str, now: float) -> None:
        q = self._load_attempts(session_id)
        while q and now - q[0] > settings.prompt_injection_window_seconds:
            q.popleft()
        self._save_attempts(session_id, q)

    def is_quarantined(self, session_id: str) -> int:
        now = time.time()
        until = float(state_store.get_json(f"{self.quarantine_prefix}{session_id}") or 0.0)
        if until > now:
            return int(until - now)
        state_store.set_json(f"{self.quarantine_prefix}{session_id}", 0.0, settings.prompt_injection_quarantine_seconds)
        return 0

    def record_injection_attempt(self, session_id: str) -> bool:
        now = time.time()
        self._evict_old_attempts(session_id, now)
        q = self._load_attempts(session_id)
        q.append(now)
        self._save_attempts(session_id, q)
        if settings.prompt_injection_strict_mode and len(q) >= settings.prompt_injection_max_attempts:
            state_store.set_json(
                f"{self.quarantine_prefix}{session_id}",
                now + settings.prompt_injection_quarantine_seconds,
                settings.prompt_injection_quarantine_seconds,
            )
            q.clear()
            self._save_attempts(session_id, q)
            return True
        return False


session_security_store = SessionSecurityStore()
