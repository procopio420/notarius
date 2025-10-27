"""
Crawler endpoints for LexNode service.
"""

import logging
import time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.database import get_db
from ..services.crawler import CrawlerService
from ..services.normalizer import NormalizerService
from ..services.indexer import IndexerService

router = APIRouter()
logger = logging.getLogger(__name__)


class CrawlRequest(BaseModel):
    """Request model for starting a crawl job."""
    source: str = Field(..., description="Source to crawl (cnj, cgj_rj)")
    base_url: Optional[str] = Field(None, description="Base URL to crawl")


class CrawlResponse(BaseModel):
    """Response model for crawl job."""
    job_id: str = Field(..., description="Crawl job ID")
    status: str = Field(..., description="Job status")
    message: str = Field(..., description="Status message")


class CrawlStatusResponse(BaseModel):
    """Response model for crawl job status."""
    job_id: str = Field(..., description="Crawl job ID")
    status: str = Field(..., description="Job status")
    documents_found: int = Field(..., description="Number of documents found")
    documents_processed: int = Field(..., description="Number of documents processed")
    error_message: Optional[str] = Field(None, description="Error message if any")


# Initialize services
crawler_service = CrawlerService()
normalizer_service = NormalizerService()
indexer_service = IndexerService()


@router.post("/crawl", response_model=CrawlResponse)
async def start_crawl(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Start a crawl job."""
    try:
        # Validate source
        if request.source not in ["cnj", "cgj_rj"]:
            raise HTTPException(status_code=400, detail="Invalid source. Must be 'cnj' or 'cgj_rj'")
        
        # Start background crawl task
        job_id = f"crawl_{request.source}_{int(time.time())}"
        background_tasks.add_task(
            _run_crawl_job,
            job_id=job_id,
            source=request.source,
            base_url=request.base_url,
            db=db
        )
        
        logger.info(f"Crawl job started: {job_id} for {request.source}")
        
        return CrawlResponse(
            job_id=job_id,
            status="started",
            message=f"Crawl job started for {request.source}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start crawl job: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start crawl job")


@router.get("/crawl/{job_id}/status", response_model=CrawlStatusResponse)
async def get_crawl_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get crawl job status."""
    try:
        # In a real implementation, this would query the database for job status
        # For now, return a mock response
        
        return CrawlStatusResponse(
            job_id=job_id,
            status="running",
            documents_found=0,
            documents_processed=0,
            error_message=None
        )
        
    except Exception as e:
        logger.error("Failed to get crawl status", error=str(e), job_id=job_id)
        raise HTTPException(status_code=500, detail="Failed to get crawl status")


@router.get("/crawl/sources")
async def list_crawl_sources():
    """List available crawl sources."""
    return {
        "sources": [
            {
                "id": "cnj",
                "name": "Conselho Nacional de Justiça",
                "description": "Federal legal documents and resolutions",
                "base_url": "https://www.cnj.jus.br",
                "jurisdiction": "federal"
            },
            {
                "id": "cgj_rj",
                "name": "Corregedoria Geral de Justiça - RJ",
                "description": "Rio de Janeiro state legal documents",
                "base_url": "https://www.tjrj.jus.br",
                "jurisdiction": "RJ"
            }
        ]
    }


async def _run_crawl_job(
    job_id: str,
    source: str,
    base_url: Optional[str],
    db: AsyncSession
):
    """Run a crawl job in the background."""
    try:
        logger.info(f"Starting crawl job: {job_id} for {source}")
        
        # Crawl documents
        documents = await crawler_service.crawl_source(source, max_documents=100)
        
        # Normalize and index
        indexed_count = 0
        for doc in documents:
            try:
                # Normalize
                normalized = normalizer_service.normalize_document(doc)
                
                # Index
                await indexer_service.index_document(db, normalized)
                indexed_count += 1
            except Exception as e:
                logger.error(f"Failed to process document: {e}")
        
        logger.info(f"Crawl job completed: {job_id}, indexed {indexed_count}/{len(documents)} documents")
        
    except Exception as e:
        logger.error(f"Crawl job failed: {job_id}, error: {e}", exc_info=True)
