"""Rate limiting and API key rotation utilities."""

import logging
import threading
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter for API calls.

    Limits the number of requests per minute to avoid hitting
    API rate limits.
    """

    def __init__(self, max_requests_per_minute: int) -> None:
        """Initialize the rate limiter.

        Args:
            max_requests_per_minute: Maximum allowed requests per minute.
        """
        self._max_rpm = max_requests_per_minute
        self._interval = 60.0 / max_requests_per_minute
        self._last_request_time = 0.0
        self._lock = threading.Lock()

    def acquire(self) -> bool:
        """Try to acquire a rate limit token without blocking.

        Returns:
            True if a token was acquired, False if rate limited.
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed >= self._interval:
                self._last_request_time = now
                return True
            return False

    def wait(self) -> None:
        """Block until a rate limit token is available."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < self._interval:
                sleep_time = self._interval - elapsed
                logger.debug("Rate limiter: sleeping %.2fs", sleep_time)
                time.sleep(sleep_time)
            self._last_request_time = time.monotonic()


class KeyRotator:
    """Round-robin API key rotator with failure tracking.

    Rotates through a pool of API keys and tracks which keys
    have failed to avoid reusing them.
    """

    def __init__(self, keys: list[str]) -> None:
        """Initialize the key rotator.

        Args:
            keys: List of API keys to rotate through.
        """
        if not keys:
            logger.warning("KeyRotator initialized with no keys")
        self._keys = list(keys)
        self._failed_keys: set[str] = set()
        self._index = 0
        self._lock = threading.Lock()

    def get_next(self) -> str:
        """Get the next available API key.

        Skips keys that have been marked as failed. If all keys are
        failed, resets the failure list and tries again.

        Returns:
            An API key string.

        Raises:
            ValueError: If no API keys are configured.
        """
        with self._lock:
            if not self._keys:
                raise ValueError("No API keys configured")

            # If all keys failed, reset
            available = [k for k in self._keys if k not in self._failed_keys]
            if not available:
                logger.warning(
                    "All %d API keys marked as failed, resetting failure list",
                    len(self._keys),
                )
                self._failed_keys.clear()
                available = self._keys

            # Round-robin through available keys
            self._index = self._index % len(available)
            key = available[self._index]
            self._index += 1
            return key

    def mark_failed(self, key: str) -> None:
        """Mark an API key as failed.

        Args:
            key: The API key that failed.
        """
        with self._lock:
            self._failed_keys.add(key)
            logger.warning(
                "API key marked as failed (ending ...%s). %d/%d keys failed.",
                key[-4:] if len(key) >= 4 else "****",
                len(self._failed_keys),
                len(self._keys),
            )
