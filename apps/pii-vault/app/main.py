"""
PII Vault FastAPI application.
Provides secure PII storage, tokenization, and encryption.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

# Add root directory to Python path to enable packages import
# This is needed because packages is at /packages, and Python needs / in path
if '/' not in sys.path:
    sys.path.insert(0, '/')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import health, vault, tokenizer, metrics
from .services.database import init_database
from packages.core.http_client import init_http_client, cleanup_http_client

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting PII Vault service")
    
    # Initialize services
    await init_http_client()
    await init_database()
    
    logger.info("PII Vault service started successfully")
    
    yield
    
    logger.info("Shutting down PII Vault service")
    await cleanup_http_client()


# Create FastAPI app
app = FastAPI(
    title="PII Vault Service",
    description="Secure PII storage, tokenization, and encryption",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(metrics.router, tags=["metrics"])
app.include_router(vault.router, prefix="/api/v1", tags=["vault"])
app.include_router(tokenizer.router, prefix="/api/v1", tags=["tokenizer"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
