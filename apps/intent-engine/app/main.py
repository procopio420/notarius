"""
Intent Engine FastAPI application.
Provides NLP intent parsing, draft generation, and PII extraction.
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

from .routes import health, intent, draft, pii_extraction, rewrite, trellis, metrics
# OpenAI client is now handled by LLMService
from .services.llm import init_llm
from .services.rewrite_service import init_rewrite_service
from .services.trellis import init_trellis
from packages.core.http_client import init_http_client, cleanup_http_client
from packages.core.service_base import initialize_all_services, cleanup_all_services

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Intent Engine service")
    
    # Initialize services
    await init_http_client()
    await initialize_all_services()
    await init_trellis()
    
    logger.info("Intent Engine service started successfully")
    
    yield
    
    logger.info("Shutting down Intent Engine service")
    await cleanup_all_services()
    await cleanup_http_client()


# Create FastAPI app
app = FastAPI(
    title="Intent Engine Service",
    description="NLP intent parsing and draft generation",
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
app.include_router(intent.router, prefix="/api/v1", tags=["intent"])
app.include_router(draft.router, prefix="/api/v1", tags=["draft"])
app.include_router(pii_extraction.router, prefix="/api/v1", tags=["pii"])
app.include_router(rewrite.router, prefix="/api/v1", tags=["rewrite"])
app.include_router(trellis.router, prefix="/api/v1/trellis", tags=["trellis"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
