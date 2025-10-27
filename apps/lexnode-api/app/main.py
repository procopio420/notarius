"""
LexNode RAG FastAPI application.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import retrieval, health, crawler, indexer
from .services.database import init_database
from .services.embeddings import init_embeddings
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
    logger.info("Starting LexNode RAG service")
    
    # Initialize services
    await init_http_client()
    await init_database()
    await init_embeddings()
    
    logger.info("LexNode RAG service started successfully")
    
    yield
    
    logger.info("Shutting down LexNode RAG service")
    await cleanup_http_client()


# Create FastAPI app
app = FastAPI(
    title="LexNode RAG Service",
    description="Legal document retrieval and grounding with hybrid search",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(retrieval.router, prefix="/api/v1/lexnode", tags=["retrieval"])
app.include_router(crawler.router, prefix="/api/v1/lexnode", tags=["crawler"])
app.include_router(indexer.router, prefix="/api/v1/lexnode", tags=["indexer"])


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
