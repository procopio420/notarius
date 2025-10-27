"""
OpenTelemetry tracing setup for all services
"""

import os
import logging
from typing import Optional, Dict, Any
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.auto_instrumentation import sitecustomize

logger = logging.getLogger(__name__)


class TracingSetup:
    """OpenTelemetry tracing configuration for all services."""
    
    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.tracer = None
        self._setup_tracing()
    
    def _setup_tracing(self):
        """Initialize OpenTelemetry tracing."""
        try:
            # Create resource
            resource = Resource.create({
                "service.name": self.service_name,
                "service.version": self.service_version,
                "deployment.environment": os.getenv("ENVIRONMENT", "development"),
            })
            
            # Set up tracer provider
            trace.set_tracer_provider(TracerProvider(resource=resource))
            tracer_provider = trace.get_tracer_provider()
            
            # Set up OTLP exporter
            otlp_endpoint = os.getenv("OTLP_ENDPOINT", "http://jaeger:4317")
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                insecure=True,
            )
            
            # Add span processor
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)
            
            # Get tracer
            self.tracer = trace.get_tracer(__name__)
            
            logger.info(f"OpenTelemetry tracing initialized for {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry tracing: {e}")
            # Fallback to no-op tracer
            self.tracer = trace.NoOpTracer()
    
    def get_tracer(self):
        """Get the configured tracer."""
        return self.tracer
    
    def create_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Create a new span with the given name and attributes."""
        if attributes is None:
            attributes = {}
        
        return self.tracer.start_span(name, attributes=attributes)
    
    def add_span_attributes(self, span, attributes: Dict[str, Any]):
        """Add attributes to a span."""
        for key, value in attributes.items():
            span.set_attribute(key, value)
    
    def add_span_event(self, span, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add an event to a span."""
        if attributes is None:
            attributes = {}
        span.add_event(name, attributes=attributes)
    
    def set_span_status(self, span, status_code: str, description: str = ""):
        """Set the status of a span."""
        from opentelemetry.trace import Status, StatusCode
        
        if status_code == "OK":
            span.set_status(Status(StatusCode.OK, description))
        elif status_code == "ERROR":
            span.set_status(Status(StatusCode.ERROR, description))
        else:
            span.set_status(Status(StatusCode.UNSET, description))


# Global tracing setup instances
_tracing_setups: Dict[str, TracingSetup] = {}


def get_tracing_setup(service_name: str) -> TracingSetup:
    """Get or create a tracing setup for a service."""
    if service_name not in _tracing_setups:
        _tracing_setups[service_name] = TracingSetup(service_name)
    return _tracing_setups[service_name]


def get_tracer(service_name: str):
    """Get a tracer for a service."""
    return get_tracing_setup(service_name).get_tracer()


def create_span(service_name: str, name: str, attributes: Optional[Dict[str, Any]] = None):
    """Create a span for a service."""
    return get_tracing_setup(service_name).create_span(name, attributes)


def trace_function(service_name: str, span_name: Optional[str] = None):
    """Decorator to trace function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = get_tracer(service_name)
            name = span_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    raise
        
        return wrapper
    return decorator


def trace_async_function(service_name: str, span_name: Optional[str] = None):
    """Decorator to trace async function execution."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            tracer = get_tracer(service_name)
            name = span_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(name) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.set_attribute("error", True)
                    span.set_attribute("error.message", str(e))
                    raise
        
        return wrapper
    return decorator


def setup_tracing(service_name: str, service_version: str = "1.0.0"):
    """Setup tracing for a service."""
    get_tracing_setup(service_name)
    logger.info(f"Tracing setup complete for {service_name}")