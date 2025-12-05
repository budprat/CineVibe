"""
Logging Utilities for CineVibe
Provides structured logging with correlation IDs and context
"""

import logging
import json
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional
import functools
import traceback

# Context variable for correlation ID (thread-safe)
_correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID"""
    return _correlation_id.get()


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set correlation ID for the current context.
    Generates a new one if not provided.
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())[:8]
    _correlation_id.set(correlation_id)
    return correlation_id


def generate_correlation_id() -> str:
    """Generate a new correlation ID"""
    return str(uuid.uuid4())[:8]


class CorrelationIdFilter(logging.Filter):
    """Logging filter that adds correlation ID to log records"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = get_correlation_id() or "no-correlation"
        return True


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    Useful for log aggregation systems like Cloud Logging.
    """

    def __init__(
        self,
        include_timestamp: bool = True,
        include_level: bool = True,
        include_logger: bool = True,
        include_correlation_id: bool = True,
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        super().__init__()
        self.include_timestamp = include_timestamp
        self.include_level = include_level
        self.include_logger = include_logger
        self.include_correlation_id = include_correlation_id
        self.extra_fields = extra_fields or {}

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "message": record.getMessage(),
        }

        if self.include_timestamp:
            log_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

        if self.include_level:
            log_data["level"] = record.levelname
            log_data["severity"] = record.levelname  # For Google Cloud Logging

        if self.include_logger:
            log_data["logger"] = record.name

        if self.include_correlation_id:
            log_data["correlation_id"] = getattr(record, "correlation_id", None)

        # Add extra fields from record
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        # Add static extra fields
        log_data.update(self.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add source location
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        return json.dumps(log_data)


class HumanReadableFormatter(logging.Formatter):
    """Human-readable formatter with colors for development"""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        correlation_id = getattr(record, "correlation_id", "no-correlation")

        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        message = record.getMessage()

        formatted = (
            f"{color}{timestamp}{reset} "
            f"[{color}{record.levelname:8}{reset}] "
            f"[{correlation_id}] "
            f"{record.name}: {message}"
        )

        if record.exc_info:
            formatted += "\n" + "".join(
                traceback.format_exception(*record.exc_info)
            )

        return formatted


def setup_logging(
    level: str = "INFO",
    structured: bool = False,
    service_name: str = "cinevibe",
    include_console: bool = True,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure logging for CineVibe services.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        structured: Use JSON structured logging (for production)
        service_name: Name of the service for log context
        include_console: Include console handler
        log_file: Optional file path for file logging

    Returns:
        Configured logger
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Create correlation ID filter
    correlation_filter = CorrelationIdFilter()

    if include_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.addFilter(correlation_filter)

        if structured:
            formatter = StructuredFormatter(
                extra_fields={"service": service_name}
            )
        else:
            formatter = HumanReadableFormatter()

        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.addFilter(correlation_filter)
        file_handler.setFormatter(StructuredFormatter(
            extra_fields={"service": service_name}
        ))
        logger.addHandler(file_handler)

    return logger


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **extra_data
):
    """
    Log message with additional context data.

    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        **extra_data: Additional data to include in log
    """
    log_level = getattr(logging, level.upper())

    # Create record with extra data
    record = logger.makeRecord(
        logger.name,
        log_level,
        "(unknown)",
        0,
        message,
        (),
        None,
    )
    record.extra_data = extra_data

    logger.handle(record)


def log_function_call(
    logger: Optional[logging.Logger] = None,
    log_args: bool = True,
    log_result: bool = False,
    log_time: bool = True,
):
    """
    Decorator for logging function calls.

    Args:
        logger: Logger to use (defaults to function's module logger)
        log_args: Log function arguments
        log_result: Log function return value
        log_time: Log execution time
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__qualname__
            start_time = datetime.utcnow()

            log_data = {"function": func_name}
            if log_args:
                log_data["args"] = str(args)[:200]
                log_data["kwargs"] = str(kwargs)[:200]

            logger.debug(f"Calling {func_name}", extra={"extra_data": log_data})

            try:
                result = await func(*args, **kwargs)

                if log_time:
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    log_data["elapsed_seconds"] = elapsed

                if log_result:
                    log_data["result"] = str(result)[:200]

                logger.debug(f"Completed {func_name}", extra={"extra_data": log_data})
                return result

            except Exception as e:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                log_data["elapsed_seconds"] = elapsed
                log_data["error"] = str(e)

                logger.error(
                    f"Error in {func_name}: {e}",
                    extra={"extra_data": log_data},
                    exc_info=True
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__qualname__
            start_time = datetime.utcnow()

            log_data = {"function": func_name}
            if log_args:
                log_data["args"] = str(args)[:200]
                log_data["kwargs"] = str(kwargs)[:200]

            logger.debug(f"Calling {func_name}", extra={"extra_data": log_data})

            try:
                result = func(*args, **kwargs)

                if log_time:
                    elapsed = (datetime.utcnow() - start_time).total_seconds()
                    log_data["elapsed_seconds"] = elapsed

                if log_result:
                    log_data["result"] = str(result)[:200]

                logger.debug(f"Completed {func_name}", extra={"extra_data": log_data})
                return result

            except Exception as e:
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                log_data["elapsed_seconds"] = elapsed
                log_data["error"] = str(e)

                logger.error(
                    f"Error in {func_name}: {e}",
                    extra={"extra_data": log_data},
                    exc_info=True
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class AgentLogger:
    """
    Specialized logger for agent operations.
    Provides structured logging for agent tasks and A2A communication.
    """

    def __init__(self, agent_name: str, logger: Optional[logging.Logger] = None):
        self.agent_name = agent_name
        self.logger = logger or logging.getLogger(f"cinevibe.agents.{agent_name}")

    def log_task_start(self, task_type: str, task_id: str, **extra):
        """Log start of agent task"""
        self.logger.info(
            f"Starting task: {task_type}",
            extra={"extra_data": {
                "agent": self.agent_name,
                "task_type": task_type,
                "task_id": task_id,
                "status": "started",
                **extra
            }}
        )

    def log_task_complete(self, task_type: str, task_id: str, duration_ms: float, **extra):
        """Log completion of agent task"""
        self.logger.info(
            f"Completed task: {task_type}",
            extra={"extra_data": {
                "agent": self.agent_name,
                "task_type": task_type,
                "task_id": task_id,
                "status": "completed",
                "duration_ms": duration_ms,
                **extra
            }}
        )

    def log_task_error(self, task_type: str, task_id: str, error: Exception, **extra):
        """Log task error"""
        self.logger.error(
            f"Task failed: {task_type} - {error}",
            extra={"extra_data": {
                "agent": self.agent_name,
                "task_type": task_type,
                "task_id": task_id,
                "status": "failed",
                "error_type": type(error).__name__,
                "error_message": str(error),
                **extra
            }},
            exc_info=True
        )

    def log_a2a_send(self, target_agent: str, task_type: str, **extra):
        """Log A2A message sent"""
        self.logger.debug(
            f"Sending A2A message to {target_agent}",
            extra={"extra_data": {
                "agent": self.agent_name,
                "target_agent": target_agent,
                "task_type": task_type,
                "direction": "outbound",
                **extra
            }}
        )

    def log_a2a_receive(self, source_agent: str, task_type: str, **extra):
        """Log A2A message received"""
        self.logger.debug(
            f"Received A2A message from {source_agent}",
            extra={"extra_data": {
                "agent": self.agent_name,
                "source_agent": source_agent,
                "task_type": task_type,
                "direction": "inbound",
                **extra
            }}
        )

    def log_generation(self, platform: str, content_type: str, duration_ms: float, **extra):
        """Log content generation"""
        self.logger.info(
            f"Generated {content_type} using {platform}",
            extra={"extra_data": {
                "agent": self.agent_name,
                "platform": platform,
                "content_type": content_type,
                "duration_ms": duration_ms,
                **extra
            }}
        )
