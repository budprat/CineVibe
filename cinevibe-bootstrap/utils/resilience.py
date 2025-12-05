"""
Resilience Patterns for CineVibe
Provides retry logic, circuit breakers, rate limiting, and bulkhead patterns
"""

import asyncio
import functools
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union
import threading
from collections import deque

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: tuple = (Exception,)
    non_retryable_exceptions: tuple = ()


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,),
    non_retryable_exceptions: tuple = (),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff calculation
        jitter: Add random jitter to prevent thundering herd
        retryable_exceptions: Tuple of exceptions to retry on
        non_retryable_exceptions: Tuple of exceptions to NOT retry on
        on_retry: Callback function called on each retry (exception, attempt)

    Example:
        @retry_with_backoff(max_attempts=3, base_delay=2.0)
        async def fetch_data():
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except non_retryable_exceptions as e:
                    logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                    raise
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Max retries ({max_attempts}) exceeded for {func.__name__}: {e}"
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )

                    # Add jitter (±25%)
                    if jitter:
                        import random
                        delay *= (0.75 + random.random() * 0.5)

                    logger.warning(
                        f"Retry {attempt}/{max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s due to: {e}"
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    await asyncio.sleep(delay)

            raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except non_retryable_exceptions as e:
                    logger.error(f"Non-retryable exception in {func.__name__}: {e}")
                    raise
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            f"Max retries ({max_attempts}) exceeded for {func.__name__}: {e}"
                        )
                        raise

                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )

                    if jitter:
                        import random
                        delay *= (0.75 + random.random() * 0.5)

                    logger.warning(
                        f"Retry {attempt}/{max_attempts} for {func.__name__} "
                        f"after {delay:.2f}s due to: {e}"
                    )

                    if on_retry:
                        on_retry(e, attempt)

                    time.sleep(delay)

            raise last_exception

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


@dataclass
class CircuitBreaker:
    """
    Circuit breaker pattern implementation.

    Prevents cascading failures by failing fast when a service is unavailable.

    States:
        CLOSED: Normal operation, requests pass through
        OPEN: Service failing, reject requests immediately
        HALF_OPEN: Testing if service recovered

    Example:
        breaker = CircuitBreaker(name="runway_api", failure_threshold=5)

        @breaker
        async def call_runway_api():
            ...
    """
    name: str
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout: float = 30.0  # Seconds before trying again

    # Internal state
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _last_failure_time: Optional[datetime] = field(default=None, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for timeout"""
        with self._lock:
            if self._state == CircuitState.OPEN:
                if self._last_failure_time:
                    elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                    if elapsed >= self.timeout:
                        self._state = CircuitState.HALF_OPEN
                        self._success_count = 0
                        logger.info(f"Circuit breaker '{self.name}' entering HALF_OPEN state")
            return self._state

    def record_success(self):
        """Record a successful call"""
        with self._lock:
            self._failure_count = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CircuitState.CLOSED
                    logger.info(f"Circuit breaker '{self.name}' CLOSED - service recovered")

    def record_failure(self, exception: Exception):
        """Record a failed call"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.name}' OPEN - failure in half-open state")
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    f"Circuit breaker '{self.name}' OPEN - "
                    f"threshold ({self.failure_threshold}) reached"
                )

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator for protecting functions with circuit breaker"""
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            if self.state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN - service unavailable"
                )

            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure(e)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            if self.state == CircuitState.OPEN:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN - service unavailable"
                )

            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure(e)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None,
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and rejects requests"""
    pass


# Pre-configured circuit breakers for each platform
circuit_breaker = {
    "runway": CircuitBreaker(name="runway", failure_threshold=5, timeout=60.0),
    "pika": CircuitBreaker(name="pika", failure_threshold=5, timeout=60.0),
    "sora": CircuitBreaker(name="sora", failure_threshold=3, timeout=120.0),
    "veo2": CircuitBreaker(name="veo2", failure_threshold=5, timeout=90.0),
    "midjourney": CircuitBreaker(name="midjourney", failure_threshold=5, timeout=60.0),
    "stable_diffusion": CircuitBreaker(name="stable_diffusion", failure_threshold=10, timeout=30.0),
    "spanner": CircuitBreaker(name="spanner", failure_threshold=3, timeout=30.0),
}


@dataclass
class RateLimiter:
    """
    Token bucket rate limiter.

    Prevents overwhelming external services with too many requests.

    Example:
        limiter = RateLimiter(rate=10, per=60)  # 10 requests per minute

        if limiter.acquire():
            await make_request()
    """
    rate: int  # Number of requests allowed
    per: float  # Time period in seconds

    _tokens: float = field(default=0.0, init=False)
    _last_update: float = field(default_factory=time.time, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)

    def __post_init__(self):
        self._tokens = float(self.rate)

    def _add_tokens(self):
        """Add tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self._last_update
        self._last_update = now

        # Add tokens proportional to elapsed time
        self._tokens = min(
            self.rate,
            self._tokens + (elapsed * self.rate / self.per)
        )

    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens for a request.

        Returns:
            True if tokens were acquired, False if rate limited
        """
        with self._lock:
            self._add_tokens()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    async def wait_for_token(self, tokens: int = 1):
        """Wait until tokens are available"""
        while not self.acquire(tokens):
            await asyncio.sleep(self.per / self.rate)

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get estimated wait time for tokens"""
        with self._lock:
            self._add_tokens()

            if self._tokens >= tokens:
                return 0.0

            needed = tokens - self._tokens
            return (needed / self.rate) * self.per


@dataclass
class BulkheadPattern:
    """
    Bulkhead pattern for isolating failures.

    Limits concurrent executions to prevent resource exhaustion.

    Example:
        bulkhead = BulkheadPattern(max_concurrent=10, max_queue=100)

        async with bulkhead:
            await process_request()
    """
    max_concurrent: int = 10
    max_queue: int = 100
    timeout: float = 30.0

    _semaphore: asyncio.Semaphore = field(default=None, init=False)
    _queue_size: int = field(default=0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    _active_count: int = field(default=0, init=False)

    def __post_init__(self):
        self._semaphore = asyncio.Semaphore(self.max_concurrent)

    async def __aenter__(self):
        with self._lock:
            if self._queue_size >= self.max_queue:
                raise BulkheadFullError(
                    f"Bulkhead queue full ({self.max_queue})"
                )
            self._queue_size += 1

        try:
            await asyncio.wait_for(
                self._semaphore.acquire(),
                timeout=self.timeout
            )
            with self._lock:
                self._active_count += 1
            return self
        except asyncio.TimeoutError:
            with self._lock:
                self._queue_size -= 1
            raise BulkheadTimeoutError(
                f"Bulkhead timeout after {self.timeout}s"
            )

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._semaphore.release()
        with self._lock:
            self._queue_size -= 1
            self._active_count -= 1

    def get_stats(self) -> Dict[str, Any]:
        """Get bulkhead statistics"""
        return {
            "max_concurrent": self.max_concurrent,
            "active": self._active_count,
            "queued": self._queue_size,
            "available": self.max_concurrent - self._active_count,
        }


class BulkheadFullError(Exception):
    """Raised when bulkhead queue is full"""
    pass


class BulkheadTimeoutError(Exception):
    """Raised when waiting for bulkhead times out"""
    pass


class FallbackHandler:
    """
    Fallback handler for graceful degradation.

    Example:
        fallback = FallbackHandler()

        @fallback.with_fallback(lambda: "default_value")
        async def get_data():
            ...
    """

    def __init__(self):
        self._fallback_counts: Dict[str, int] = {}

    def with_fallback(
        self,
        fallback_func: Callable[[], T],
        exceptions: tuple = (Exception,)
    ):
        """Decorator to add fallback behavior"""
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> T:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(
                        f"Falling back for {func.__name__} due to: {e}"
                    )
                    self._fallback_counts[func.__name__] = \
                        self._fallback_counts.get(func.__name__, 0) + 1
                    return fallback_func()

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> T:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    logger.warning(
                        f"Falling back for {func.__name__} due to: {e}"
                    )
                    self._fallback_counts[func.__name__] = \
                        self._fallback_counts.get(func.__name__, 0) + 1
                    return fallback_func()

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper

        return decorator


async def with_timeout(
    coro,
    timeout: float,
    timeout_message: str = "Operation timed out"
) -> Any:
    """
    Execute coroutine with timeout.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        timeout_message: Message for TimeoutError

    Raises:
        TimeoutError: If operation exceeds timeout
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        raise TimeoutError(timeout_message)
