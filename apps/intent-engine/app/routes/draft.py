"""
Draft generation API endpoints.
"""

import logging
import uuid
from typing import Dict, Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.draft_generator import DraftGenerator

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class GenerateDraftRequest(BaseModel):
    """Request to generate draft."""
    parsed_intent: Dict = Field(..., description="Parsed intent structure")
    template_content: Optional[str] = Field(None, description="Optional template")
    legal_citations: Optional[List[Dict]] = Field(None, description="Optional legal citations")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: str = Field(..., description="User ID")


class GenerateDraftResponse(BaseModel):
    """Response from draft generation."""
    draft_id: str
    content: str
    placeholders: List[str]
    citations: List[Dict]
    grounding_confidence: float
    metadata: Dict


# Initialize draft generator
draft_generator = DraftGenerator()


@router.post("/generate-draft", response_model=GenerateDraftResponse)
async def generate_draft(request: GenerateDraftRequest):
    """
    Generate document draft from parsed intent.
    """
    try:
        # Validate input
        if not request.parsed_intent:
            raise HTTPException(status_code=400, detail="Parsed intent is required")
        
        # Generate draft
        draft = await draft_generator.generate_draft(
            parsed_intent=request.parsed_intent,
            template_content=request.template_content,
            legal_citations=request.legal_citations,
        )
        
        # Generate draft ID
        draft_id = str(uuid.uuid4())
        
        return GenerateDraftResponse(
            draft_id=draft_id,
            content=draft["content"],
            placeholders=draft["placeholders"],
            citations=draft["citations"],
            grounding_confidence=draft["grounding_confidence"],
            metadata=draft["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate draft: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate draft")

