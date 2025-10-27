"""
Database connection and session management.
"""

import os
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from ..models.vault import Base

logger = logging.getLogger(__name__)

# Database engine
engine = None
async_session_factory = None


async def init_database():
    """Initialize database connection."""
    global engine, async_session_factory
    
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://vault:vault_dev@postgres-vault:5432/vault_db")
    
    # Convert postgresql:// to postgresql+asyncpg://
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    logger.info(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    
    engine = create_async_engine(
        database_url,
        poolclass=NullPool,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    )
    
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database initialized successfully")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
