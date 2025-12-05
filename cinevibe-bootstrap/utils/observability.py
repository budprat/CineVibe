"""
Observability Module for CineVibe
Provides OpenTelemetry tracing, Prometheus metrics, and health monitoring
"""

import os
import time
import functools
import logging
from typing import Any, Callable, Dict, Optional, TypeVar
from datetime import datetime
from dataclasses import dataclass, field
from contextlib import contextmanager
import threading
import json

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ==========================================
# Metrics Collection
# ==========================================

@dataclass
class Counter:
    """Simple counter metric"""
    name: str
    description: str
    labels: Dict[str, str] = field(default_factory=dict)
    _value: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def inc(self, amount: float = 1.0):
        with self._lock:
            self._value += amount

    def get(self) -> float:
        return self._value


@dataclass
class Gauge:
    """Simple gauge metric"""
    name: str
    description: str
    labels: Dict[str, str] = field(default_factory=dict)
    _value: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def set(self, value: float):
        with self._lock:
            self._value = value

    def inc(self, amount: float = 1.0):
        with self._lock:
            self._value += amount

    def dec(self, amount: float = 1.0):
        with self._lock:
            self._value -= amount

    def get(self) -> float:
        return self._value


@dataclass
class Histogram:
    """Simple histogram metric with predefined buckets"""
    name: str
    description: str
    buckets: tuple = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10)
    labels: Dict[str, str] = field(default_factory=dict)
    _values: list = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def observe(self, value: float):
        with self._lock:
            self._values.append(value)

    def get_percentile(self, percentile: float) -> float:
        if not self._values:
            return 0.0
        sorted_values = sorted(self._values)
        idx = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(idx, len(sorted_values) - 1)]

    def get_count(self) -> int:
        return len(self._values)

    def get_sum(self) -> float:
        return sum(self._values)


class MetricsRegistry:
    """Central registry for all metrics"""

    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def counter(self, name: str, description: str, labels: Dict[str, str] = None) -> Counter:
        """Get or create a counter"""
        key = f"counter_{name}"
        with self._lock:
            if key not in self._metrics:
                self._metrics[key] = Counter(name, description, labels or {})
            return self._metrics[key]

    def gauge(self, name: str, description: str, labels: Dict[str, str] = None) -> Gauge:
        """Get or create a gauge"""
        key = f"gauge_{name}"
        with self._lock:
            if key not in self._metrics:
                self._metrics[key] = Gauge(name, description, labels or {})
            return self._metrics[key]

    def histogram(self, name: str, description: str, buckets: tuple = None, labels: Dict[str, str] = None) -> Histogram:
        """Get or create a histogram"""
        key = f"histogram_{name}"
        with self._lock:
            if key not in self._metrics:
                self._metrics[key] = Histogram(
                    name, description,
                    buckets=buckets or (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
                    labels=labels or {}
                )
            return self._metrics[key]

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics for export"""
        result = {}
        with self._lock:
            for key, metric in self._metrics.items():
                if isinstance(metric, Counter):
                    result[key] = {"type": "counter", "value": metric.get()}
                elif isinstance(metric, Gauge):
                    result[key] = {"type": "gauge", "value": metric.get()}
                elif isinstance(metric, Histogram):
                    result[key] = {
                        "type": "histogram",
                        "count": metric.get_count(),
                        "sum": metric.get_sum(),
                        "p50": metric.get_percentile(50),
                        "p95": metric.get_percentile(95),
                        "p99": metric.get_percentile(99),
                    }
        return result

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        with self._lock:
            for key, metric in self._metrics.items():
                if isinstance(metric, Counter):
                    lines.append(f"# HELP {metric.name} {metric.description}")
                    lines.append(f"# TYPE {metric.name} counter")
                    lines.append(f"{metric.name} {metric.get()}")
                elif isinstance(metric, Gauge):
                    lines.append(f"# HELP {metric.name} {metric.description}")
                    lines.append(f"# TYPE {metric.name} gauge")
                    lines.append(f"{metric.name} {metric.get()}")
                elif isinstance(metric, Histogram):
                    lines.append(f"# HELP {metric.name} {metric.description}")
                    lines.append(f"# TYPE {metric.name} histogram")
                    lines.append(f"{metric.name}_count {metric.get_count()}")
                    lines.append(f"{metric.name}_sum {metric.get_sum()}")
        return "\n".join(lines)


# Global metrics registry
metrics = MetricsRegistry()


# ==========================================
# CineVibe-specific Metrics
# ==========================================

# Generation metrics
generation_requests_total = metrics.counter(
    "cinevibe_generation_requests_total",
    "Total number of generation requests"
)
generation_duration_seconds = metrics.histogram(
    "cinevibe_generation_duration_seconds",
    "Time spent generating content"
)
generation_errors_total = metrics.counter(
    "cinevibe_generation_errors_total",
    "Total number of generation errors"
)
generation_cost_usd = metrics.counter(
    "cinevibe_generation_cost_usd",
    "Total generation cost in USD"
)

# Agent metrics
agent_tasks_total = metrics.counter(
    "cinevibe_agent_tasks_total",
    "Total number of agent tasks processed"
)
agent_task_duration_seconds = metrics.histogram(
    "cinevibe_agent_task_duration_seconds",
    "Time spent processing agent tasks"
)
active_agents = metrics.gauge(
    "cinevibe_active_agents",
    "Number of active agents"
)

# Pipeline metrics
pipeline_executions_total = metrics.counter(
    "cinevibe_pipeline_executions_total",
    "Total number of pipeline executions"
)
pipeline_phase_duration_seconds = metrics.histogram(
    "cinevibe_pipeline_phase_duration_seconds",
    "Time spent in each pipeline phase"
)

# Database metrics
db_queries_total = metrics.counter(
    "cinevibe_db_queries_total",
    "Total number of database queries"
)
db_query_duration_seconds = metrics.histogram(
    "cinevibe_db_query_duration_seconds",
    "Time spent on database queries"
)

# API metrics
api_requests_total = metrics.counter(
    "cinevibe_api_requests_total",
    "Total number of API requests"
)
api_request_duration_seconds = metrics.histogram(
    "cinevibe_api_request_duration_seconds",
    "Time spent processing API requests"
)


# ==========================================
# Tracing
# ==========================================

@dataclass
class Span:
    """Simple span for tracing"""
    trace_id: str
    span_id: str
    name: str
    service_name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: str = "OK"
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: list = field(default_factory=list)
    parent_span_id: Optional[str] = None

    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        })

    def set_status(self, status: str, message: str = ""):
        self.status = status
        if message:
            self.attributes["status_message"] = message

    def end(self):
        self.end_time = time.time()

    def to_dict(self) -> Dict:
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "service_name": self.service_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": (self.end_time - self.start_time) * 1000 if self.end_time else None,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events
        }


class Tracer:
    """Simple tracer for distributed tracing"""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._current_span: Optional[Span] = None
        self._spans: list = []
        self._lock = threading.Lock()

    def _generate_id(self) -> str:
        import uuid
        return uuid.uuid4().hex[:16]

    @contextmanager
    def start_span(self, name: str, attributes: Dict[str, Any] = None):
        """Start a new span as context manager"""
        trace_id = self._generate_id()
        span_id = self._generate_id()
        parent_span_id = self._current_span.span_id if self._current_span else None

        span = Span(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            service_name=self.service_name,
            parent_span_id=parent_span_id,
            attributes=attributes or {}
        )

        old_span = self._current_span
        self._current_span = span

        try:
            yield span
            span.set_status("OK")
        except Exception as e:
            span.set_status("ERROR", str(e))
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e))
            raise
        finally:
            span.end()
            with self._lock:
                self._spans.append(span)
            self._current_span = old_span

    def get_spans(self) -> list:
        """Get all recorded spans"""
        with self._lock:
            return [s.to_dict() for s in self._spans]

    def clear_spans(self):
        """Clear recorded spans"""
        with self._lock:
            self._spans.clear()


# Global tracers for each service
tracers: Dict[str, Tracer] = {}


def get_tracer(service_name: str) -> Tracer:
    """Get or create tracer for a service"""
    if service_name not in tracers:
        tracers[service_name] = Tracer(service_name)
    return tracers[service_name]


# ==========================================
# Instrumentation Decorators
# ==========================================

def instrument(
    name: Optional[str] = None,
    service_name: str = "cinevibe",
    record_args: bool = False,
    record_result: bool = False
):
    """
    Decorator to instrument functions with tracing and metrics.

    Example:
        @instrument(name="process_script", service_name="script_analyzer")
        async def process_script(script_id: str):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        span_name = name or func.__qualname__
        tracer = get_tracer(service_name)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            with tracer.start_span(span_name) as span:
                if record_args:
                    span.set_attribute("args", str(args)[:500])
                    span.set_attribute("kwargs", str(kwargs)[:500])

                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    if record_result:
                        span.set_attribute("result", str(result)[:500])
                    return result
                finally:
                    duration = time.time() - start
                    agent_task_duration_seconds.observe(duration)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            with tracer.start_span(span_name) as span:
                if record_args:
                    span.set_attribute("args", str(args)[:500])
                    span.set_attribute("kwargs", str(kwargs)[:500])

                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    if record_result:
                        span.set_attribute("result", str(result)[:500])
                    return result
                finally:
                    duration = time.time() - start
                    agent_task_duration_seconds.observe(duration)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def track_generation(platform: str, content_type: str):
    """
    Decorator to track generation metrics.

    Example:
        @track_generation(platform="runway", content_type="video")
        async def generate_video(prompt: str):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            generation_requests_total.inc()

            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                generation_duration_seconds.observe(duration)
                return result
            except Exception as e:
                generation_errors_total.inc()
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            generation_requests_total.inc()

            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                generation_duration_seconds.observe(duration)
                return result
            except Exception as e:
                generation_errors_total.inc()
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ==========================================
# Health Check
# ==========================================

@dataclass
class HealthStatus:
    """Health status for a component"""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "checked_at": self.checked_at.isoformat()
        }


class HealthChecker:
    """Aggregate health checker for all components"""

    def __init__(self):
        self._checks: Dict[str, Callable] = {}

    def register_check(self, name: str, check_func: Callable[[], HealthStatus]):
        """Register a health check function"""
        self._checks[name] = check_func

    async def check_all(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {}
        overall_status = "healthy"

        for name, check_func in self._checks.items():
            try:
                import asyncio
                if asyncio.iscoroutinefunction(check_func):
                    status = await check_func()
                else:
                    status = check_func()

                results[name] = status.to_dict()

                if status.status == "unhealthy":
                    overall_status = "unhealthy"
                elif status.status == "degraded" and overall_status == "healthy":
                    overall_status = "degraded"

            except Exception as e:
                results[name] = HealthStatus(
                    name=name,
                    status="unhealthy",
                    message=str(e)
                ).to_dict()
                overall_status = "unhealthy"

        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": results
        }


# Global health checker
health_checker = HealthChecker()


# ==========================================
# Export Endpoints
# ==========================================

def get_metrics_endpoint():
    """FastAPI endpoint for metrics"""
    from fastapi import APIRouter
    from fastapi.responses import PlainTextResponse

    router = APIRouter()

    @router.get("/metrics")
    async def metrics_endpoint():
        return PlainTextResponse(
            content=metrics.export_prometheus(),
            media_type="text/plain"
        )

    @router.get("/metrics/json")
    async def metrics_json():
        return metrics.get_all_metrics()

    return router


def get_health_endpoint():
    """FastAPI endpoint for health checks"""
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/health")
    async def health_endpoint():
        return await health_checker.check_all()

    @router.get("/health/live")
    async def liveness():
        return {"status": "alive"}

    @router.get("/health/ready")
    async def readiness():
        result = await health_checker.check_all()
        return {"status": "ready" if result["status"] != "unhealthy" else "not_ready"}

    return router
