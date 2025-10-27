"""
Document rewrite API endpoints.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.rewrite_service import get_rewrite_service

router = APIRouter()
logger = logging.getLogger(__name__)


# Request/Response models
class RewriteContentRequest(BaseModel):
    """Request to rewrite document content."""
    content: str = Field(..., description="Original document content to rewrite")
    improvement_prompt: str = Field(..., description="User's improvement request")
    document_type: str = Field(default="procuracao", description="Type of document")
    preserve_variables: bool = Field(default=True, description="Whether to preserve {{VARIABLE}} placeholders")
    tenant_id: Optional[str] = Field(None, description="Tenant ID for tracking")
    user_id: Optional[str] = Field(None, description="User ID for tracking")


class RewriteContentResponse(BaseModel):
    """Response from content rewriting."""
    rewritten_content: str
    confidence: float
    tokens_used: int
    model_used: str
    provider: str
    variables_preserved: int
    improvement_applied: str
    original_length: int
    rewritten_length: int


@router.post("/rewrite-content", response_model=RewriteContentResponse)
async def rewrite_content(request: RewriteContentRequest):
    """
    Rewrite document content using AI based on improvement prompt.
    """
    try:
        # Validate input
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="Content is required")
        
        if not request.improvement_prompt.strip():
            raise HTTPException(status_code=400, detail="Improvement prompt is required")
        
        # Get rewrite service
        rewrite_service = get_rewrite_service()
        
        # Rewrite content
        result = await rewrite_service.rewrite_content(
            content=request.content,
            improvement_prompt=request.improvement_prompt,
            document_type=request.document_type,
            preserve_variables=request.preserve_variables,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
        )
        
        return RewriteContentResponse(
            rewritten_content=result["rewritten_content"],
            confidence=result["confidence"],
            tokens_used=result["tokens_used"],
            model_used=result["model_used"],
            provider=result["provider"],
            variables_preserved=result["variables_preserved"],
            improvement_applied=result["improvement_applied"],
            original_length=result["original_length"],
            rewritten_length=result["rewritten_length"],
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rewrite content: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to rewrite content")


@router.get("/rewrite/health")
async def rewrite_health():
    """Health check for rewrite service."""
    try:
        rewrite_service = get_rewrite_service()
        return {"status": "healthy", "service": "rewrite"}
    except Exception as e:
        logger.error(f"Rewrite service health check failed: {e}")
        raise HTTPException(status_code=503, detail="Rewrite service unavailable")
