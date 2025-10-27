"""
Observability package for Privacy-First AI Notarius.

Provides OpenTelemetry tracing, structured logging, metrics collection,
and correlation ID propagation across all services.
"""

from .tracing import (
    setup_tracing,
    get_tracer,
    trace_function,
    trace_async_function,
)

from .logging import (
    setup_logging,
    get_logger,
    log_with_context,
    LogContext,
)

from .metrics import (
    setup_metrics,
    get_metrics_collector,
    MetricsCollector,
)

from .correlation import (
    setup_correlation,
    get_correlation_id,
    set_correlation_id,
    CorrelationMiddleware,
)

__all__ = [
    # Tracing
    "setup_tracing",
    "get_tracer",
    "trace_function",
    "trace_async_function",
    
    # Logging
    "setup_logging",
    "get_logger",
    "log_with_context",
    "LogContext",
    
    # Metrics
    "setup_metrics",
    "get_metrics_collector",
    "MetricsCollector",
    
    # Correlation
    "setup_correlation",
    "get_correlation_id",
    "set_correlation_id",
    "CorrelationMiddleware",
]
