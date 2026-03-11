from __future__ import annotations

import time
from collections import defaultdict, deque

from app.core.config import settings


class DDoSGuard:
    def __init__(self) -> None:
        self.violations: dict[str, deque[float]] = defaultdict(deque)
        self.blocked_until: dict[str, float] = {}

    def _evict_old(self, ip: str, now: float) -> None:
        q = self.violations[ip]
        while q and now - q[0] > settings.ddos_block_window_seconds:
            q.popleft()

    def is_blocked(self, ip: str) -> int:
        now = time.time()
        until = self.blocked_until.get(ip, 0.0)
        if until > now:
            return int(until - now)
        if ip in self.blocked_until:
            del self.blocked_until[ip]
        return 0

    def record_violation(self, ip: str) -> None:
        now = time.time()
        self._evict_old(ip, now)
        q = self.violations[ip]
        q.append(now)
        if len(q) >= settings.ddos_block_after_violations:
            self.blocked_until[ip] = now + settings.ddos_block_duration_seconds
            q.clear()


ddos_guard = DDoSGuard()
