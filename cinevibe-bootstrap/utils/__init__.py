"""
CineVibe Utilities Package
Shared utilities for error handling, resilience, logging, and validation
"""

from .resilience import (
    retry_with_backoff,
    CircuitBreaker,
    circuit_breaker,
    RateLimiter,
    BulkheadPattern,
)
from .logging_utils import (
    setup_logging,
    get_correlation_id,
    set_correlation_id,
    CorrelationIdFilter,
    log_with_context,
)
from .validation import (
    TaskInput,
    ScriptAnalysisInput,
    CharacterDNAInput,
    GenerationRequest,
    A2ATaskRequest,
    A2ATaskResponse,
    validate_input,
)

__all__ = [
    # Resilience
    "retry_with_backoff",
    "CircuitBreaker",
    "circuit_breaker",
    "RateLimiter",
    "BulkheadPattern",
    # Logging
    "setup_logging",
    "get_correlation_id",
    "set_correlation_id",
    "CorrelationIdFilter",
    "log_with_context",
    # Validation
    "TaskInput",
    "ScriptAnalysisInput",
    "CharacterDNAInput",
    "GenerationRequest",
    "A2ATaskRequest",
    "A2ATaskResponse",
    "validate_input",
]
