"""
Intent parsing API endpoints.
"""

import logging
import uuid
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..services.intent_parser import IntentParser

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class ParseIntentRequest(BaseModel):
    """Request to parse intent."""
    intent: str = Field(..., description="Natural language intent in Portuguese")
    processo_id: Optional[str] = Field(None, description="Associated processo ID")
    tenant_id: str = Field(..., description="Tenant ID")
    user_id: str = Field(..., description="User ID")
    context: Optional[Dict] = Field(None, description="Additional context")


class ParseIntentResponse(BaseModel):
    """Response from intent parsing."""
    intent_id: str
    parsed_intent: Dict
    confidence: float
    suggestions: list


class ValidateIntentRequest(BaseModel):
    """Request to validate intent."""
    intent: str = Field(..., description="Natural language intent")
    document_type: str = Field(..., description="Expected document type")


class ValidateIntentResponse(BaseModel):
    """Response from intent validation."""
    is_valid: bool
    confidence: float
    errors: list
    suggestions: list


# Initialize intent parser
intent_parser = IntentParser()


@router.post("/parse-intent", response_model=ParseIntentResponse)
async def parse_intent(request: ParseIntentRequest):
    """
    Parse natural language intent into structured data.
    """
    try:
        # Validate input
        if not request.intent or not request.intent.strip():
            raise HTTPException(status_code=400, detail="Intent cannot be empty")
        
        # Build context
        context = request.context or {}
        context.update({
            "processo_id": request.processo_id,
            "tenant_id": request.tenant_id,
            "user_id": request.user_id,
        })
        
        # Parse intent
        parsed = await intent_parser.parse_intent(
            intent_text=request.intent,
            context=context
        )
        
        # Generate intent ID
        intent_id = str(uuid.uuid4())
        
        return ParseIntentResponse(
            intent_id=intent_id,
            parsed_intent=parsed,
            confidence=parsed.get("confidence", 0.0),
            suggestions=parsed.get("suggestions", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to parse intent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to parse intent")


@router.post("/validate-intent", response_model=ValidateIntentResponse)
async def validate_intent(request: ValidateIntentRequest):
    """
    Validate if intent is appropriate for document type.
    """
    try:
        if not request.intent or not request.intent.strip():
            raise HTTPException(status_code=400, detail="Intent cannot be empty")
        
        validation = await intent_parser.validate_intent(
            intent_text=request.intent,
            document_type=request.document_type
        )
        
        return ValidateIntentResponse(**validation)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate intent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to validate intent")


@router.get("/document-types")
async def get_supported_document_types():
    """
    Get list of supported document types.
    """
    return {
        "document_types": [
            {
                "type": "procuracao",
                "name": "Procuração",
                "description": "Documento de procuração (power of attorney)",
                "supported_actions": ["create", "modify", "revoke"]
            },
            {
                "type": "certidao",
                "name": "Certidão",
                "description": "Documento de certidão (certificate)",
                "supported_actions": ["create", "modify"]
            },
            {
                "type": "testamento",
                "name": "Testamento",
                "description": "Documento de testamento (will)",
                "supported_actions": ["create", "modify", "revoke"]
            },
            {
                "type": "escritura",
                "name": "Escritura",
                "description": "Documento de escritura (deed)",
                "supported_actions": ["create", "modify"]
            },
            {
                "type": "contrato",
                "name": "Contrato",
                "description": "Documento de contrato (contract)",
                "supported_actions": ["create", "modify", "cancel"]
            },
        ]
    }


@router.get("/intent-templates")
async def get_intent_templates():
    """
    Get example intent templates.
    """
    return {
        "templates": [
            {
                "id": "procuracao_basica",
                "name": "Procuração Básica",
                "description": "Template para procuração básica",
                "document_type": "procuracao",
                "example": "Criar uma procuração para [OUTORGANTE] representar [OUTORGADO] em [OBJETO]"
            },
            {
                "id": "procuracao_compra_venda",
                "name": "Procuração para Compra e Venda",
                "description": "Template para procuração de compra e venda de imóvel",
                "document_type": "procuracao",
                "example": "Criar uma procuração para [OUTORGANTE] representar [OUTORGADO] em uma compra e venda de imóvel no valor de R$ [VALOR]"
            },
            {
                "id": "certidao_nascimento",
                "name": "Certidão de Nascimento",
                "description": "Template para certidão de nascimento",
                "document_type": "certidao",
                "example": "Criar uma certidão de nascimento para [NOME], nascido em [DATA_NASCIMENTO], filho de [NOME_PAI] e [NOME_MAE]"
            },
        ]
    }
