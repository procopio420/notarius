"""
Correlation ID propagation and middleware.
"""

import uuid
from contextvars import ContextVar
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable for correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def setup_correlation() -> None:
    """Setup correlation ID handling."""
    pass  # No setup needed for context variables


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return correlation_id.get()


def set_correlation_id(corr_id: str) -> None:
    """Set the correlation ID in context."""
    correlation_id.set(corr_id)


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


class CorrelationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle correlation ID propagation."""
    
    def __init__(self, app, header_name: str = "X-Correlation-ID"):
        super().__init__(app)
        self.header_name = header_name
    
    async def dispatch(self, request: Request, call_next):
        # Get correlation ID from header or generate new one
        corr_id = request.headers.get(self.header_name)
        if not corr_id:
            corr_id = generate_correlation_id()
        
        # Set in context
        set_correlation_id(corr_id)
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers[self.header_name] = corr_id
        
        return response


class CorrelationContext:
    """Context manager for correlation ID operations."""
    
    def __init__(self, corr_id: Optional[str] = None):
        self.corr_id = corr_id or generate_correlation_id()
        self.previous_corr_id = None
    
    def __enter__(self):
        # Store previous correlation ID
        self.previous_corr_id = get_correlation_id()
        
        # Set new correlation ID
        set_correlation_id(self.corr_id)
        
        return self.corr_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous correlation ID
        if self.previous_corr_id:
            set_correlation_id(self.previous_corr_id)
        else:
            correlation_id.set(None)
