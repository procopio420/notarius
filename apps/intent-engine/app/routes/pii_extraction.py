"""
PII extraction API endpoints.
"""

import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from packages.pii.extractors import MultiLayerPIIExtractor

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class ExtractPIIRequest(BaseModel):
    """Request to extract PII."""
    text: str = Field(..., description="Text to extract PII from")
    pii_types: Optional[List[str]] = Field(None, description="Specific PII types to extract")


class ExtractPIIResponse(BaseModel):
    """Response from PII extraction."""
    extracted_pii: Dict[str, List[str]]
    confidence: float
    pii_count: int


# Initialize PII extractor
pii_extractor = MultiLayerPIIExtractor()


@router.post("/extract-pii", response_model=ExtractPIIResponse)
async def extract_pii(request: ExtractPIIRequest):
    """
    Extract PII from text.
    """
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Text cannot be empty")
        
        # Extract PII using the shared multi-layer extractor
        pii_entities = await pii_extractor.extract(request.text)
        
        # Convert to the expected format
        extracted = {}
        for entity in pii_entities:
            entity_type = entity.type.value
            if entity_type not in extracted:
                extracted[entity_type] = []
            extracted[entity_type].append(entity.value)
        
        # Calculate confidence based on number of matches
        pii_count = sum(len(values) for values in extracted.values())
        confidence = min(0.5 + (pii_count * 0.1), 0.95)  # Higher confidence with more PIIs found
        
        return ExtractPIIResponse(
            extracted_pii=extracted,
            confidence=confidence,
            pii_count=pii_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extract PII: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to extract PII")

