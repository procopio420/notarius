"""
Centralized HTTP client with connection pooling and lifecycle management.

This module provides a singleton HTTP client manager that handles:
- Connection pooling across all requests
- Automatic correlation ID injection
- Request/response logging
- Metrics collection integration
- Proper resource cleanup
"""

import asyncio
import logging
import time
from typing import Dict, Optional, Any, Union
from contextlib import asynccontextmanager

import httpx
from packages.observability import get_logger, get_metrics_collector
from packages.observability.correlation import get_correlation_id

logger = get_logger(__name__)


class HTTPClientManager:
    """Centralized HTTP client with connection pooling and lifecycle management."""
    
    def __init__(self, service_name: str = "default-service"):
        self._client: Optional[httpx.AsyncClient] = None
        self._metrics = get_metrics_collector(service_name)
        self._is_initialized = False
    
    async def initialize(self, 
                        timeout: float = 30.0,
                        limits: httpx.Limits = None,
                        retries: int = 3) -> None:
        """Initialize the HTTP client with configuration."""
        if self._is_initialized:
            logger.warning("HTTP client already initialized")
            return
        
        # Default limits if not provided
        if limits is None:
            limits = httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100,
                keepalive_expiry=30.0
            )
        
        # Create client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
            headers={
                "User-Agent": "Notarius/1.0.0",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        
        self._is_initialized = True
        logger.info("HTTP client initialized with connection pooling")
    
    async def cleanup(self) -> None:
        """Cleanup HTTP client resources."""
        if self._client:
            await self._client.aclose()
            self._client = None
            self._is_initialized = False
            logger.info("HTTP client cleaned up")
    
    def _ensure_initialized(self) -> httpx.AsyncClient:
        """Ensure client is initialized."""
        if not self._is_initialized or not self._client:
            raise RuntimeError("HTTP client not initialized. Call initialize() first.")
        return self._client
    
    async def request(self,
                     method: str,
                     url: str,
                     **kwargs) -> httpx.Response:
        """
        Make an HTTP request with automatic correlation ID injection and logging.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            **kwargs: Additional httpx request parameters
            
        Returns:
            httpx.Response object
        """
        client = self._ensure_initialized()
        
        # Inject correlation ID
        headers = kwargs.get('headers', {})
        correlation_id = get_correlation_id()
        if correlation_id:
            headers['X-Correlation-ID'] = correlation_id
        kwargs['headers'] = headers
        
        # Add request ID for tracing
        request_id = f"req_{int(time.time() * 1000)}"
        headers['X-Request-ID'] = request_id
        
        # Log request
        logger.debug(
            "Making HTTP request",
            method=method,
            url=url,
            request_id=request_id,
            correlation_id=correlation_id
        )
        
        start_time = time.time()
        
        try:
            response = await client.request(method, url, **kwargs)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log response
            logger.debug(
                "HTTP request completed",
                method=method,
                url=url,
                status_code=response.status_code,
                duration_ms=int(duration * 1000),
                request_id=request_id
            )
            
            # Record metrics
            self._metrics.record_http_request(
                method=method,
                url=url,
                status_code=response.status_code,
                duration_ms=int(duration * 1000),
                request_id=request_id
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            logger.error(
                "HTTP request failed",
                method=method,
                url=url,
                error=str(e),
                duration_ms=int(duration * 1000),
                request_id=request_id,
                exc_info=True
            )
            
            # Record error metrics
            self._metrics.record_http_error(
                method=method,
                url=url,
                error_type=type(e).__name__,
                duration_ms=int(duration * 1000),
                request_id=request_id
            )
            
            raise
    
    async def get(self, url: str, **kwargs) -> httpx.Response:
        """Make a GET request."""
        return await self.request("GET", url, **kwargs)
    
    async def post(self, url: str, **kwargs) -> httpx.Response:
        """Make a POST request."""
        return await self.request("POST", url, **kwargs)
    
    async def put(self, url: str, **kwargs) -> httpx.Response:
        """Make a PUT request."""
        return await self.request("PUT", url, **kwargs)
    
    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """Make a DELETE request."""
        return await self.request("DELETE", url, **kwargs)
    
    async def patch(self, url: str, **kwargs) -> httpx.Response:
        """Make a PATCH request."""
        return await self.request("PATCH", url, **kwargs)
    
    @asynccontextmanager
    async def stream(self, method: str, url: str, **kwargs):
        """Stream an HTTP request."""
        client = self._ensure_initialized()
        
        # Inject correlation ID
        headers = kwargs.get('headers', {})
        correlation_id = get_correlation_id()
        if correlation_id:
            headers['X-Correlation-ID'] = correlation_id
        kwargs['headers'] = headers
        
        async with client.stream(method, url, **kwargs) as response:
            yield response


# Global singleton instance
_http_client_manager: Optional[HTTPClientManager] = None


async def init_http_client(timeout: float = 30.0,
                          limits: httpx.Limits = None,
                          retries: int = 3,
                          service_name: str = "default-service") -> None:
    """Initialize the global HTTP client manager."""
    global _http_client_manager
    
    if _http_client_manager is None:
        _http_client_manager = HTTPClientManager(service_name)
    
    await _http_client_manager.initialize(timeout, limits, retries)
    logger.info("Global HTTP client manager initialized")


async def cleanup_http_client() -> None:
    """Cleanup the global HTTP client manager."""
    global _http_client_manager
    
    if _http_client_manager:
        await _http_client_manager.cleanup()
        _http_client_manager = None


def get_http_client() -> HTTPClientManager:
    """Get the global HTTP client manager instance."""
    if _http_client_manager is None:
        raise RuntimeError("HTTP client not initialized. Call init_http_client() first.")
    return _http_client_manager


# Convenience functions for common operations
async def get(url: str, **kwargs) -> httpx.Response:
    """Make a GET request using the global client."""
    return await get_http_client().get(url, **kwargs)


async def post(url: str, **kwargs) -> httpx.Response:
    """Make a POST request using the global client."""
    return await get_http_client().post(url, **kwargs)


async def put(url: str, **kwargs) -> httpx.Response:
    """Make a PUT request using the global client."""
    return await get_http_client().put(url, **kwargs)


async def delete(url: str, **kwargs) -> httpx.Response:
    """Make a DELETE request using the global client."""
    return await get_http_client().delete(url, **kwargs)


async def patch(url: str, **kwargs) -> httpx.Response:
    """Make a PATCH request using the global client."""
    return await get_http_client().patch(url, **kwargs)
