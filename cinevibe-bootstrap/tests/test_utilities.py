"""
Tests for CineVibe Utilities
Tests resilience patterns, logging, and validation schemas
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.resilience import (
    retry_with_backoff,
    CircuitBreaker,
    CircuitState,
    CircuitBreakerOpenError,
    RateLimiter,
    BulkheadPattern,
    BulkheadFullError,
)
from utils.logging_utils import (
    get_correlation_id,
    set_correlation_id,
    generate_correlation_id,
    AgentLogger,
)
from utils.validation import (
    CharacterDNAInput,
    ScriptAnalysisInput,
    GenerationRequest,
    A2ATaskRequest,
    ContentType,
    Platform,
    TaskStatus,
)


# ==========================================
# Resilience Tests
# ==========================================

class TestRetryWithBackoff:
    """Tests for retry decorator"""

    def test_successful_call_no_retry(self):
        """Test that successful calls don't retry"""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = success_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_failure(self):
        """Test retry on failure"""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = failing_func()
        assert result == "success"
        assert call_count == 3

    def test_max_retries_exceeded(self):
        """Test that exception is raised after max retries"""
        @retry_with_backoff(max_attempts=2, base_delay=0.01)
        def always_fails():
            raise ConnectionError("Network error")

        with pytest.raises(ConnectionError):
            always_fails()

    def test_non_retryable_exception(self):
        """Test non-retryable exceptions are raised immediately"""
        call_count = 0

        @retry_with_backoff(
            max_attempts=3,
            base_delay=0.01,
            non_retryable_exceptions=(ValueError,)
        )
        def func_with_value_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Not retryable")

        with pytest.raises(ValueError):
            func_with_value_error()

        assert call_count == 1  # Should not retry

    @pytest.mark.asyncio
    async def test_async_retry(self):
        """Test async function retry"""
        call_count = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        async def async_failing():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise IOError("Async error")
            return "async_success"

        result = await async_failing()
        assert result == "async_success"
        assert call_count == 2


class TestCircuitBreaker:
    """Tests for circuit breaker pattern"""

    def test_initial_state_closed(self):
        """Test circuit starts in closed state"""
        breaker = CircuitBreaker(name="test", failure_threshold=3)
        assert breaker.state == CircuitState.CLOSED

    def test_opens_after_threshold(self):
        """Test circuit opens after failure threshold"""
        breaker = CircuitBreaker(name="test", failure_threshold=2, timeout=0.1)

        @breaker
        def failing_func():
            raise RuntimeError("Test error")

        # Fail twice to open circuit
        for _ in range(2):
            try:
                failing_func()
            except RuntimeError:
                pass

        assert breaker.state == CircuitState.OPEN

    def test_rejects_when_open(self):
        """Test circuit rejects calls when open"""
        breaker = CircuitBreaker(name="test", failure_threshold=1, timeout=60)

        @breaker
        def func():
            raise RuntimeError("Error")

        # Open the circuit
        try:
            func()
        except RuntimeError:
            pass

        # Should raise CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            func()

    def test_half_open_after_timeout(self):
        """Test circuit enters half-open after timeout"""
        breaker = CircuitBreaker(name="test", failure_threshold=1, timeout=0.1)

        @breaker
        def func():
            raise RuntimeError("Error")

        # Open circuit
        try:
            func()
        except RuntimeError:
            pass

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(0.15)

        assert breaker.state == CircuitState.HALF_OPEN

    def test_closes_after_success_in_half_open(self):
        """Test circuit closes after success in half-open state"""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=1,
            success_threshold=1,
            timeout=0.1
        )

        call_count = 0

        @breaker
        def func():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("First call fails")
            return "success"

        # Open circuit
        try:
            func()
        except RuntimeError:
            pass

        # Wait for half-open
        time.sleep(0.15)

        # Success should close circuit
        result = func()
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED


class TestRateLimiter:
    """Tests for rate limiter"""

    def test_allows_within_limit(self):
        """Test allows requests within rate limit"""
        limiter = RateLimiter(rate=5, per=1.0)

        # Should allow 5 requests immediately
        for _ in range(5):
            assert limiter.acquire() is True

    def test_rejects_over_limit(self):
        """Test rejects requests over rate limit"""
        limiter = RateLimiter(rate=2, per=1.0)

        assert limiter.acquire() is True
        assert limiter.acquire() is True
        assert limiter.acquire() is False  # Third should fail

    def test_tokens_refill_over_time(self):
        """Test tokens refill over time"""
        limiter = RateLimiter(rate=10, per=0.1)

        # Use all tokens
        for _ in range(10):
            limiter.acquire()

        assert limiter.acquire() is False

        # Wait for refill
        time.sleep(0.15)

        assert limiter.acquire() is True


class TestBulkheadPattern:
    """Tests for bulkhead pattern"""

    @pytest.mark.asyncio
    async def test_limits_concurrent_execution(self):
        """Test bulkhead limits concurrent executions"""
        bulkhead = BulkheadPattern(max_concurrent=2, max_queue=5, timeout=1.0)

        active = 0
        max_active = 0

        async def task():
            nonlocal active, max_active
            async with bulkhead:
                active += 1
                max_active = max(max_active, active)
                await asyncio.sleep(0.1)
                active -= 1

        # Run 5 tasks concurrently
        await asyncio.gather(*[task() for _ in range(5)])

        assert max_active <= 2


# ==========================================
# Logging Tests
# ==========================================

class TestLoggingUtils:
    """Tests for logging utilities"""

    def test_correlation_id_generation(self):
        """Test correlation ID generation"""
        cid = generate_correlation_id()
        assert isinstance(cid, str)
        assert len(cid) == 8

    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation ID"""
        test_id = "test1234"
        set_correlation_id(test_id)
        assert get_correlation_id() == test_id

    def test_set_correlation_id_generates_new(self):
        """Test set_correlation_id generates new ID if none provided"""
        result = set_correlation_id()
        assert result is not None
        assert len(result) == 8
        assert get_correlation_id() == result


class TestAgentLogger:
    """Tests for agent logger"""

    def test_agent_logger_creation(self):
        """Test agent logger creation"""
        logger = AgentLogger("test_agent")
        assert logger.agent_name == "test_agent"

    def test_log_task_start(self):
        """Test logging task start"""
        with patch('logging.Logger.info') as mock_info:
            logger = AgentLogger("test_agent")
            logger.log_task_start("analyze", "task123", extra_key="value")
            mock_info.assert_called_once()


# ==========================================
# Validation Tests
# ==========================================

class TestValidationSchemas:
    """Tests for Pydantic validation schemas"""

    def test_character_dna_input_valid(self):
        """Test valid CharacterDNAInput"""
        input_data = CharacterDNAInput(
            name="Sarah",
            description="A young scientist"
        )
        assert input_data.name == "SARAH"  # Should be uppercased

    def test_character_dna_input_requires_name(self):
        """Test CharacterDNAInput requires name"""
        with pytest.raises(Exception):
            CharacterDNAInput(description="No name")

    def test_script_analysis_input_valid(self):
        """Test valid ScriptAnalysisInput"""
        input_data = ScriptAnalysisInput(
            script_content="INT. OFFICE - DAY\n\nJOHN enters.",
            title="Test Script"
        )
        assert input_data.title == "Test Script"

    def test_script_analysis_input_requires_content(self):
        """Test ScriptAnalysisInput requires non-empty content"""
        with pytest.raises(Exception):
            ScriptAnalysisInput(script_content="")

    def test_generation_request_valid(self):
        """Test valid GenerationRequest"""
        request = GenerationRequest(
            prompt="A sunset over mountains",
            content_type=ContentType.IMAGE,
            platform=Platform.STABLE_DIFFUSION
        )
        assert request.prompt == "A sunset over mountains"
        assert request.content_type == ContentType.IMAGE

    def test_generation_request_video_gets_default_duration(self):
        """Test video GenerationRequest gets default duration"""
        request = GenerationRequest(
            prompt="A bird flying",
            content_type=ContentType.VIDEO
        )
        assert request.duration == 5  # Default

    def test_a2a_task_request_valid(self):
        """Test valid A2ATaskRequest"""
        request = A2ATaskRequest(
            type="analyze_script",
            input={"script": "content"}
        )
        assert request.type == "analyze_script"
        assert request.timeout == 60.0  # Default


# ==========================================
# Integration Tests
# ==========================================

class TestResilienceIntegration:
    """Integration tests for resilience patterns"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retry(self):
        """Test circuit breaker works with retry decorator"""
        breaker = CircuitBreaker(name="integration", failure_threshold=3, timeout=0.1)
        call_count = 0

        @breaker
        @retry_with_backoff(max_attempts=2, base_delay=0.01)
        async def protected_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Network error")

        # Should retry within circuit breaker
        with pytest.raises(ConnectionError):
            await protected_func()

        assert call_count == 2  # Retried once


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
