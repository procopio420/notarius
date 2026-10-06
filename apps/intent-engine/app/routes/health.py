"""
Health check endpoints for Intent Engine service.
"""

import sys
import os

# Ensure root directory is in path to enable packages import
if '/' not in sys.path:
    sys.path.insert(0, '/')

from fastapi import APIRouter
from fastapi.responses import Response
from packages.core.service_base import health_check_all_services
from packages.observability.metrics import get_metrics_collector

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
