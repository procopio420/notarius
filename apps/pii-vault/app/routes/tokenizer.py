"""
Tokenizer API endpoints.
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.database import get_db
from ..services.vault import VaultService

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class TokenizeRequest(BaseModel):
    """Request to tokenize PII."""
    pii_data: Dict[str, str] = Field(..., description="Dict of PII type to value")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: Optional[str] = Field(None, description="User ID")


class TokenizeResponse(BaseModel):
    """Response from tokenization."""
    tokens: Dict[str, str] = Field(..., description="Dict of PII type to token")
    hashes: Dict[str, str] = Field(..., description="Dict of PII type to hash")


class DetokenizeRequest(BaseModel):
    """Request to detokenize."""
    tokens: Dict[str, str] = Field(..., description="Dict of field name to token")
    tenant_id: str = Field(..., description="Tenant ID")


class DetokenizeResponse(BaseModel):
    """Response from detokenization."""
    pii_data: Dict[str, Optional[str]]


class GeneratePlaceholderRequest(BaseModel):
    """Request to generate placeholder."""
    pii_type: str = Field(..., description="Type of PII")
    index: int = Field(0, description="Index for multiple values")


class GeneratePlaceholderResponse(BaseModel):
    """Response with placeholder."""
    placeholder: str


# Initialize vault service
vault_service = VaultService()


@router.post("/tokenize", response_model=TokenizeResponse)
async def tokenize(
    request: TokenizeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Tokenize multiple PII values at once.
    """
    try:
        tokens = {}
        hashes = {}
        
        for pii_type, pii_value in request.pii_data.items():
            if not pii_value:  # Skip empty values
                continue
                
            result = await vault_service.store_pii(
                db=db,
                pii_value=pii_value,
                pii_type=pii_type,
                tenant_id=request.tenant_id,
                user_id=request.user_id,
            )
            
            tokens[pii_type] = result["token"]
            hashes[pii_type] = result["hash"]
        
        return TokenizeResponse(tokens=tokens, hashes=hashes)
        
    except Exception as e:
        logger.error(f"Failed to tokenize: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to tokenize PII")


@router.post("/detokenize", response_model=DetokenizeResponse)
async def detokenize(
    request: DetokenizeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Detokenize multiple tokens at once.
    """
    try:
        pii_data = {}
        
        for field_name, token in request.tokens.items():
            if not token:  # Skip empty tokens
                pii_data[field_name] = None
                continue
            
            pii_value = await vault_service.retrieve_pii(
                db=db,
                token=token,
                tenant_id=request.tenant_id,
            )
            
            pii_data[field_name] = pii_value
        
        return DetokenizeResponse(pii_data=pii_data)
        
    except Exception as e:
        logger.error(f"Failed to detokenize: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to detokenize")


@router.post("/generate-placeholder", response_model=GeneratePlaceholderResponse)
async def generate_placeholder(request: GeneratePlaceholderRequest):
    """
    Generate placeholder for PII type.
    """
    try:
        placeholder = vault_service.tokenizer_service.generate_placeholder(
            pii_type=request.pii_type,
            index=request.index
        )
        
        return GeneratePlaceholderResponse(placeholder=placeholder)
        
    except Exception as e:
        logger.error(f"Failed to generate placeholder: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate placeholder")


@router.post("/validate-token")
async def validate_token(token: str):
    """
    Validate token format.
    """
    try:
        is_valid = vault_service.tokenizer_service.validate_token_format(token)
        pii_type = vault_service.tokenizer_service.extract_pii_type_from_token(token)
        
        return {
            "token": token,
            "valid": is_valid,
            "pii_type": pii_type
        }
        
    except Exception as e:
        logger.error(f"Failed to validate token: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to validate token")

