"""Simple token-bucket rate limiter for async HTTP calls."""

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator


class RateLimiter:
    """Async rate limiter combining a token bucket with a concurrency semaphore.

    Parameters
    ----------
    requests_per_second:
        Maximum sustained request rate.
    max_concurrent:
        Maximum number of in-flight requests at any moment.
    """

    def __init__(
        self,
        requests_per_second: float = 2.0,
        max_concurrent: int = 3,
    ) -> None:
        self.interval = 1.0 / requests_per_second
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._last_request_time: float = 0.0
        self._lock = asyncio.Lock()

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[None]:
        """Context manager that blocks until the caller may proceed."""
        async with self._semaphore:
            async with self._lock:
                now = time.monotonic()
                wait = self._last_request_time + self.interval - now
                if wait > 0:
                    await asyncio.sleep(wait)
                self._last_request_time = time.monotonic()
            yield
