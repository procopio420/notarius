"""
Health check endpoints for PII Vault service.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..services.database import get_db

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check."""
    return {"status": "healthy", "service": "pii-vault"}


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Readiness check with database connectivity."""
    try:
        # Test database connection
        await db.execute(text("SELECT 1"))
        
        return {
            "status": "ready",
            "service": "pii-vault",
            "database": "connected"
        }
    except Exception as e:
        return {
            "status": "not_ready",
            "service": "pii-vault",
            "database": "disconnected",
            "error": str(e)
        }


@router.get("/live")
async def liveness_check():
    """Liveness check."""
    return {"status": "alive", "service": "pii-vault"}
