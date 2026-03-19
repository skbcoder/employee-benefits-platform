"""In-memory per-IP sliding window rate limiter."""

import asyncio
import time
from collections import defaultdict, deque


class RateLimiter:
    """Sliding window rate limiter — no external dependencies."""

    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, client_ip: str) -> bool:
        """Return True if the request is allowed, False if rate-limited."""
        async with self._lock:
            now = time.monotonic()
            window = self._requests[client_ip]
            cutoff = now - self._window_seconds

            # Evict expired entries
            while window and window[0] < cutoff:
                window.popleft()

            if len(window) >= self._max_requests:
                return False

            window.append(now)
            return True

    @property
    def window_seconds(self) -> int:
        return self._window_seconds
