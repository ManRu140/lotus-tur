"""Process-local sliding-window rate limiter.

IMPORTANT OPERATIONAL CAVEAT: this state lives in this process's memory
only. It resets on every restart/redeploy and is NOT shared across
multiple worker processes or horizontally scaled instances. For a single
Railway instance running one worker, this is a reasonable, zero-
dependency way to slow down brute force/credential stuffing. If you ever
run multiple workers or instances, replace the in-memory dict with a
shared store (e.g. Redis — `slowapi` with a redis backend is a drop-in
option) so attempts are actually counted globally, or this limiter will
undercount and give attackers `max_attempts` tries per worker.
"""

import asyncio
import time
from collections import defaultdict

from fastapi import HTTPException, status


class InMemoryRateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
        # SECURITY/RELIABILITY: keys are only ever trimmed when that same
        # key is hit again — a key for an IP/username pair that's never
        # seen twice stays in the dict forever, growing unbounded under
        # normal internet traffic (let alone an attacker deliberately
        # spraying unique IPs/usernames to exhaust memory). We bound this
        # by sweeping fully-expired keys out periodically.
        self._last_sweep = time.monotonic()
        self._sweep_interval = max(window_seconds, 60)

    async def check(self, key: str) -> None:
        """Raise 429 if `key` has exceeded the limit; otherwise record
        this attempt and return normally.
        """
        now = time.monotonic()
        async with self._lock:
            self._sweep_if_due(now)

            fresh = [t for t in self._attempts[key] if now - t < self.window_seconds]
            if len(fresh) >= self.max_attempts:
                self._attempts[key] = fresh
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Слишком много попыток. Повторите через {self.window_seconds} секунд.",
                    headers={"Retry-After": str(self.window_seconds)},
                )
            fresh.append(now)
            self._attempts[key] = fresh

    def _sweep_if_due(self, now: float) -> None:
        """Drop any key whose every recorded attempt has aged out of the
        window. Must be called with `self._lock` already held. O(n) over
        all tracked keys, so it's throttled to run at most once per
        window instead of on every request.
        """
        if now - self._last_sweep < self._sweep_interval:
            return
        self._last_sweep = now
        expired = [
            k for k, attempts in self._attempts.items()
            if not attempts or now - attempts[-1] >= self.window_seconds
        ]
        for k in expired:
            del self._attempts[k]
