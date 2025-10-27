"""
Base service class with standardized initialization and lifecycle management.

This module provides a consistent pattern for all services across the Notarius
microservices ecosystem, ensuring proper resource management and initialization.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TypeVar, Generic
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='BaseService')


class BaseService(ABC):
    """
    Base service class with standardized initialization and lifecycle management.
    
    All services should inherit from this class to ensure consistent patterns
    across the microservices ecosystem.
    """
    
    def __init__(self, dependencies: Optional[Dict[str, Any]] = None):
        """
        Initialize the service with optional dependencies.
        
        Args:
            dependencies: Dictionary of service dependencies
        """
        self.dependencies = dependencies or {}
        self._is_initialized = False
        self._is_healthy = False
        self._service_name = self.__class__.__name__
        
        logger.debug(f"Initializing {self._service_name}")
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the service and its dependencies.
        
        This method should be implemented by subclasses to perform
        any async initialization required.
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """
        Cleanup service resources.
        
        This method should be implemented by subclasses to perform
        any cleanup required when the service is shut down.
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the service.
        
        Returns:
            Dictionary containing health status information
        """
        return {
            "service": self._service_name,
            "initialized": self._is_initialized,
            "healthy": self._is_healthy,
            "dependencies": list(self.dependencies.keys())
        }
    
    def _mark_initialized(self) -> None:
        """Mark the service as initialized."""
        self._is_initialized = True
        logger.info(f"{self._service_name} initialized successfully")
    
    def _mark_healthy(self) -> None:
        """Mark the service as healthy."""
        self._is_healthy = True
        logger.debug(f"{self._service_name} is healthy")
    
    def _mark_unhealthy(self, reason: str = "Unknown") -> None:
        """Mark the service as unhealthy."""
        self._is_healthy = False
        logger.warning(f"{self._service_name} is unhealthy: {reason}")
    
    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._is_initialized
    
    @property
    def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        return self._is_healthy and self._is_initialized


class ServiceManager(Generic[T]):
    """
    Service manager for singleton pattern with proper lifecycle management.
    
    This class provides a standardized way to manage service instances
    across the microservices ecosystem.
    """
    
    def __init__(self, service_class: type[T]):
        self.service_class = service_class
        self._instance: Optional[T] = None
        self._service_name = service_class.__name__
    
    async def initialize(self, dependencies: Optional[Dict[str, Any]] = None) -> T:
        """
        Initialize the service instance.
        
        Args:
            dependencies: Optional service dependencies
            
        Returns:
            The initialized service instance
        """
        if self._instance is not None:
            logger.warning(f"{self._service_name} already initialized")
            return self._instance
        
        logger.info(f"Initializing {self._service_name}")
        self._instance = self.service_class(dependencies)
        await self._instance.initialize()
        
        return self._instance
    
    async def cleanup(self) -> None:
        """Cleanup the service instance."""
        if self._instance is not None:
            logger.info(f"Cleaning up {self._service_name}")
            await self._instance.cleanup()
            self._instance = None
    
    def get_instance(self) -> T:
        """
        Get the service instance.
        
        Returns:
            The service instance
            
        Raises:
            RuntimeError: If the service is not initialized
        """
        if self._instance is None:
            raise RuntimeError(f"{self._service_name} not initialized. Call initialize() first.")
        return self._instance
    
    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._instance is not None and self._instance.is_initialized
    
    @property
    def is_healthy(self) -> bool:
        """Check if the service is healthy."""
        return self._instance is not None and self._instance.is_healthy
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the service."""
        if self._instance is None:
            return {
                "service": self._service_name,
                "initialized": False,
                "healthy": False,
                "error": "Service not initialized"
            }
        
        return await self._instance.health_check()


# Global service managers
_service_managers: Dict[str, ServiceManager] = {}


def register_service(service_class: type[T]) -> ServiceManager[T]:
    """
    Register a service class with the global service manager.
    
    Args:
        service_class: The service class to register
        
    Returns:
        The service manager instance
    """
    service_name = service_class.__name__
    if service_name in _service_managers:
        logger.warning(f"Service {service_name} already registered")
        return _service_managers[service_name]
    
    manager = ServiceManager(service_class)
    _service_managers[service_name] = manager
    logger.debug(f"Registered service {service_name}")
    
    return manager


def get_service_manager(service_class: type[T]) -> ServiceManager[T]:
    """
    Get the service manager for a service class.
    
    Args:
        service_class: The service class
        
    Returns:
        The service manager instance
    """
    service_name = service_class.__name__
    if service_name not in _service_managers:
        return register_service(service_class)
    
    return _service_managers[service_name]


async def initialize_all_services() -> None:
    """Initialize all registered services."""
    logger.info("Initializing all registered services")
    
    for service_name, manager in _service_managers.items():
        try:
            await manager.initialize()
            logger.info(f"Service {service_name} initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize service {service_name}: {e}")
            raise


async def cleanup_all_services() -> None:
    """Cleanup all registered services."""
    logger.info("Cleaning up all registered services")
    
    for service_name, manager in _service_managers.items():
        try:
            await manager.cleanup()
            logger.info(f"Service {service_name} cleaned up successfully")
        except Exception as e:
            logger.error(f"Failed to cleanup service {service_name}: {e}")


async def health_check_all_services() -> Dict[str, Dict[str, Any]]:
    """Perform health checks on all registered services."""
    results = {}
    
    for service_name, manager in _service_managers.items():
        try:
            results[service_name] = await manager.health_check()
        except Exception as e:
            results[service_name] = {
                "service": service_name,
                "initialized": False,
                "healthy": False,
                "error": str(e)
            }
    
    return results


@asynccontextmanager
async def service_lifecycle():
    """
    Context manager for service lifecycle management.
    
    Usage:
        async with service_lifecycle():
            # Services are initialized
            service = get_service_manager(MyService).get_instance()
            # Use service
        # Services are automatically cleaned up
    """
    try:
        await initialize_all_services()
        yield
    finally:
        await cleanup_all_services()
