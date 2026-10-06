"""
Validation views.
"""

import logging
import asyncio
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Lazy import to avoid issues during Docker build
# ValidationEngine will be imported when actually needed
from .models import ValidationResult
from apps.tenancy.tenancy import get_current_tenant

logger = logging.getLogger(__name__)

# Global validation engine instance
_validation_engine = None


def get_validation_engine_sync():
    """Get or create validation engine instance (synchronous wrapper)."""
    global _validation_engine
    if _validation_engine is None:
        # Lazy import to avoid issues during Docker build
        from .services.validation_engine import ValidationEngine
        _validation_engine = ValidationEngine()
        # Initialize in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_validation_engine.initialize())
        loop.close()
    return _validation_engine


@api_view(['POST'])
def validate_document(request):
    """
    Validate document against legal rules.
    
    POST /api/v1/validation/validate-document/
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
        engine = get_validation_engine_sync()
        
        # Run async validation in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        validation_result = loop.run_until_complete(engine.validate(
            document_type=document_type,
            extracted_data=extracted_data,
            uf=uf
        ))
        loop.close()
        
        # Save result if tenant available
        tenant = getattr(request, 'tenant', None) or get_current_tenant()
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

