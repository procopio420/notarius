"""
Health check endpoints for LexNode service.
"""

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..services.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "lexnode-api"}


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check with database connectivity."""
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        
        return {
            "status": "ready",
            "service": "lexnode-api",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "service": "lexnode-api",
            "database": "disconnected",
            "error": str(e)
        }


@router.get("/live")
async def liveness_check():
    """Liveness check."""
    return {"status": "alive", "service": "lexnode-api"}
