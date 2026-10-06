"""
Validation views.
"""

import logging
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone

from .services.validation_engine import ValidationEngine
from .models import ValidationResult
from apps.base.views import get_tenant_from_request

logger = logging.getLogger(__name__)

# Global validation engine instance
_validation_engine = None


async def get_validation_engine():
    """Get or create validation engine instance."""
    global _validation_engine
    if _validation_engine is None:
        _validation_engine = ValidationEngine()
        await _validation_engine.initialize()
    return _validation_engine


@api_view(['POST'])
async def validate_document(request):
    """
    Validate document against legal rules.
    
    POST /api/v1/validate-document
    {
        "document_type": "escritura_compra_venda",
        "extracted_data": {...},
        "uf": "SP"
    }
    """
    try:
        document_type = request.data.get('document_type')
        extracted_data = request.data.get('extracted_data', {})
        uf = request.data.get('uf')
        
        if not document_type:
            return Response(
                {"error": "document_type is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get validation engine
        engine = await get_validation_engine()
        
        # Validate
        validation_result = await engine.validate(
            document_type=document_type,
            extracted_data=extracted_data,
            uf=uf
        )
        
        # Save result if tenant available
        tenant = get_tenant_from_request(request)
        if tenant:
            ValidationResult.objects.create(
                tenant=tenant,
                document_type=document_type,
                extracted_data=extracted_data,
                exigencias=validation_result.get("exigencias", []),
                bloqueantes=validation_result.get("bloqueantes", []),
                opcionais=validation_result.get("opcionais", []),
                citacoes=validation_result.get("citacoes", []),
                uf=uf
            )
        
        return Response(validation_result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

