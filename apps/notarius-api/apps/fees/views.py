"""
Fee views.
"""

import logging
from decimal import Decimal
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .services.fee_calculator import FeeCalculator
from .serializers import FeeCalculationSerializer
from apps.tenancy.tenancy import get_current_tenant

logger = logging.getLogger(__name__)


@api_view(['POST'])
def calculate_fees(request):
    """
    Calculate fees for a document type and UF.
    
    POST /api/v1/fees/calculate-fees/
    {
        "document_type": "escritura_compra_venda",
        "uf": "SP",
        "base_value": 450000.00  # Optional, for percentage calculations
    }
    """
    try:
        document_type = request.data.get('document_type')
        uf = request.data.get('uf')
        base_value = request.data.get('base_value')
        
        if not document_type:
            return Response(
                {"error": "document_type is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not uf:
            return Response(
                {"error": "uf is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert base_value to Decimal if provided
        base_decimal = None
        if base_value:
            try:
                base_decimal = Decimal(str(base_value))
            except:
                pass
        
        # Get tenant
        tenant = getattr(request, 'tenant', None) or get_current_tenant()
        
        # Calculate fees
        calculator = FeeCalculator()
        fees = calculator.calculate(
            document_type=document_type,
            uf=uf,
            base_value=base_decimal,
            tenant=tenant
        )
        
        # Serialize response
        serializer = FeeCalculationSerializer(fees)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Fee calculation failed: {e}", exc_info=True)
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

