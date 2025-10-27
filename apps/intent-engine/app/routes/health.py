"""
Health check endpoints for Intent Engine service.
"""

from fastapi import APIRouter
from packages.core.service_base import health_check_all_services

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "intent-engine"}


@router.get("/ready")
async def readiness_check():
    """Readiness check with service health status."""
    services_health = await health_check_all_services()
    
    # Check if all services are healthy
    all_healthy = all(
        service.get("healthy", False) 
        for service in services_health.values()
    )
    
    return {
        "status": "ready" if all_healthy else "not_ready",
        "service": "intent-engine",
        "services": services_health
    }


@router.get("/live")
async def liveness_check():
    """Liveness check."""
    return {"status": "alive", "service": "intent-engine"}
