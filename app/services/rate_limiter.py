from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass

from fastapi import HTTPException, status

from app.core.metrics import rate_limit_blocks_total
from app.core.config import settings
from app.services.ddos_guard import ddos_guard


@dataclass
class WindowLimit:
    window_seconds: int
    user_limit: int
    ip_limit: int
    global_limit: int


class SlidingWindowLimiter:
    def __init__(self, spec: WindowLimit) -> None:
        self.spec = spec
        self.user_events = defaultdict(deque)
        self.ip_events = defaultdict(deque)
        self.global_events = deque()

    def _evict_old(self, q: deque, now: float) -> None:
        while q and now - q[0] > self.spec.window_seconds:
            q.popleft()

    def _check_queue(self, q: deque, limit: int, now: float) -> tuple[bool, int]:
        self._evict_old(q, now)
        if len(q) >= limit:
            retry_after = int(max(1, self.spec.window_seconds - (now - q[0])))
            return False, retry_after
        return True, 0

    def check(self, user_id: str, ip: str, now: float) -> int:
        ok, retry = self._check_queue(self.user_events[user_id], self.spec.user_limit, now)
        if not ok:
            return retry
        ok, retry = self._check_queue(self.ip_events[ip], self.spec.ip_limit, now)
        if not ok:
            return retry
        ok, retry = self._check_queue(self.global_events, self.spec.global_limit, now)
        if not ok:
            return retry
        return 0

    def commit(self, user_id: str, ip: str, now: float) -> None:
        self.user_events[user_id].append(now)
        self.ip_events[ip].append(now)
        self.global_events.append(now)


class CompositeRateLimiter:
    def __init__(self) -> None:
        self.burst = SlidingWindowLimiter(
            WindowLimit(
                window_seconds=settings.burst_window_seconds,
                user_limit=settings.burst_limit_per_user,
                ip_limit=settings.burst_limit_per_ip,
                global_limit=settings.burst_limit_global
            )
        )
        self.sustained = SlidingWindowLimiter(
            WindowLimit(
                window_seconds=settings.sustained_window_seconds,
                user_limit=settings.sustained_limit_per_user,
                ip_limit=settings.sustained_limit_per_ip,
                global_limit=settings.sustained_limit_global
            )
        )

    def enforce(self, user_id: str, ip: str) -> None:
        blocked_for = ddos_guard.is_blocked(ip)
        if blocked_for > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Request limit reached. Retry in {blocked_for} seconds.",
                headers={"Retry-After": str(blocked_for)},
            )

        now = time.time()
        burst_retry = self.burst.check(user_id, ip, now)
        sustained_retry = self.sustained.check(user_id, ip, now)
        retry_after = max(burst_retry, sustained_retry)
        if retry_after > 0:
            ddos_guard.record_violation(ip)
            if burst_retry > 0:
                rate_limit_blocks_total.labels(window="burst").inc()
            if sustained_retry > 0:
                rate_limit_blocks_total.labels(window="sustained").inc()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        self.burst.commit(user_id, ip, now)
        self.sustained.commit(user_id, ip, now)


rate_limiter = CompositeRateLimiter()
