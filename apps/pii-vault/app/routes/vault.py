"""
PII Vault API endpoints.
"""

import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.database import get_db
from ..services.vault import VaultService

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class StorePIIRequest(BaseModel):
    """Request to store PII."""
    pii_value: str = Field(..., description="PII value to store")
    pii_type: str = Field(..., description="Type of PII (cpf, cnpj, nome, etc.)")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: Optional[str] = Field(None, description="User ID")
    metadata: Optional[Dict] = Field(None, description="Additional metadata")


class StorePIIResponse(BaseModel):
    """Response from storing PII."""
    record_id: str
    token: str
    hash: str
    reused: bool


class RetrievePIIRequest(BaseModel):
    """Request to retrieve PII."""
    token: str = Field(..., description="PII token")
    tenant_id: str = Field(..., description="Tenant ID")


class RetrievePIIResponse(BaseModel):
    """Response from retrieving PII."""
    token: str
    pii_value: Optional[str]
    pii_type: Optional[str]


class BatchDetokenizeRequest(BaseModel):
    """Request to detokenize multiple tokens."""
    tokens: List[str] = Field(..., description="List of tokens to detokenize")
    tenant_id: str = Field(..., description="Tenant ID")


class BatchDetokenizeResponse(BaseModel):
    """Response from batch detokenization."""
    results: Dict[str, Optional[str]]


class DeletePIIRequest(BaseModel):
    """Request to delete PII."""
    token: str = Field(..., description="PII token")
    tenant_id: str = Field(..., description="Tenant ID")


class AuditLogResponse(BaseModel):
    """Audit log response."""
    audit_log: List[Dict]
    total: int


# Initialize vault service
vault_service = VaultService()


@router.post("/store-pii", response_model=StorePIIResponse)
async def store_pii(
    request: StorePIIRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Store PII value and return token.
    """
    try:
        result = await vault_service.store_pii(
            db=db,
            pii_value=request.pii_value,
            pii_type=request.pii_type,
            tenant_id=request.tenant_id,
            user_id=request.user_id,
            metadata=request.metadata,
        )
        
        return StorePIIResponse(**result)
        
    except Exception as e:
        logger.error(f"Failed to store PII: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to store PII")


@router.post("/retrieve-pii", response_model=RetrievePIIResponse)
async def retrieve_pii(
    request: RetrievePIIRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve PII value by token.
    """
    try:
        pii_value = await vault_service.retrieve_pii(
            db=db,
            token=request.token,
            tenant_id=request.tenant_id,
        )
        
        if pii_value is None:
            raise HTTPException(status_code=404, detail="PII not found")
        
        # Extract PII type from token
        pii_type = vault_service.tokenizer_service.extract_pii_type_from_token(request.token)
        
        return RetrievePIIResponse(
            token=request.token,
            pii_value=pii_value,
            pii_type=pii_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve PII: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve PII")


@router.post("/detokenize-batch", response_model=BatchDetokenizeResponse)
async def detokenize_batch(
    request: BatchDetokenizeRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Detokenize multiple tokens in a single request.
    """
    try:
        results = await vault_service.detokenize_batch(
            db=db,
            tokens=request.tokens,
            tenant_id=request.tenant_id,
        )
        
        return BatchDetokenizeResponse(results=results)
        
    except Exception as e:
        logger.error(f"Failed to batch detokenize: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to detokenize batch")


@router.post("/delete-pii")
async def delete_pii(
    request: DeletePIIRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete PII record (soft delete).
    """
    try:
        deleted = await vault_service.delete_pii(
            db=db,
            token=request.token,
            tenant_id=request.tenant_id,
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="PII not found")
        
        return {"status": "deleted", "token": request.token}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete PII: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete PII")


@router.get("/audit-log/{tenant_id}", response_model=AuditLogResponse)
async def get_audit_log(
    tenant_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit log for tenant.
    """
    try:
        audit_log = await vault_service.get_audit_log(
            db=db,
            tenant_id=tenant_id,
            limit=limit,
        )
        
        return AuditLogResponse(
            audit_log=audit_log,
            total=len(audit_log)
        )
        
    except Exception as e:
        logger.error(f"Failed to get audit log: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get audit log")
