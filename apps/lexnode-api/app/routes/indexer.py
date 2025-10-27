"""
Indexing API endpoints.
"""

import logging
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.database import get_db
from ..services.indexer import IndexerService
from ..services.normalizer import NormalizerService

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class IndexDocumentRequest(BaseModel):
    """Request to index a document."""
    document: Dict = Field(..., description="Document to index")


class IndexDocumentResponse(BaseModel):
    """Response from indexing."""
    document_id: str
    status: str


class IndexBatchRequest(BaseModel):
    """Request to index multiple documents."""
    documents: List[Dict] = Field(..., description="Documents to index")


class IndexBatchResponse(BaseModel):
    """Response from batch indexing."""
    indexed_count: int
    failed_count: int
    document_ids: List[str]


# Initialize services
indexer_service = IndexerService()
normalizer_service = NormalizerService()


@router.post("/index", response_model=IndexDocumentResponse)
async def index_document(
    request: IndexDocumentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Index a single document.
    """
    try:
        # Normalize first
        normalized = normalizer_service.normalize_document(request.document)
        
        # Index
        doc_id = await indexer_service.index_document(db, normalized)
        
        return IndexDocumentResponse(
            document_id=doc_id,
            status="indexed"
        )
        
    except Exception as e:
        logger.error(f"Failed to index document: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to index document")


@router.post("/index-batch", response_model=IndexBatchResponse)
async def index_batch(
    request: IndexBatchRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Index multiple documents at once.
    """
    try:
        # Normalize all documents
        normalized_docs = []
        for doc in request.documents:
            normalized = normalizer_service.normalize_document(doc)
            normalized_docs.append(normalized)
        
        # Index batch
        doc_ids = await indexer_service.index_batch(db, normalized_docs)
        
        return IndexBatchResponse(
            indexed_count=len(doc_ids),
            failed_count=len(request.documents) - len(doc_ids),
            document_ids=doc_ids
        )
        
    except Exception as e:
        logger.error(f"Failed to batch index: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to batch index")

