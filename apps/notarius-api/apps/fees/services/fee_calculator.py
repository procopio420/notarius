"""
Fee calculator service for emoluments and taxes.
"""

import logging
from typing import Dict, List, Optional
from decimal import Decimal

from ..models import FeeRule

logger = logging.getLogger(__name__)


class FeeCalculator:
    """Pluggable state fee calculator."""
    
    def calculate(
        self,
        document_type: str,
        uf: str,
        base_value: Optional[Decimal] = None,
        tenant=None
    ) -> Dict:
        """
        Calculate fees for a document type in a specific UF.
        
        Args:
            document_type: Document type
            uf: State abbreviation
            base_value: Base value for percentage calculations (optional)
            tenant: Tenant for multi-tenant filtering
            
        Returns:
            Dict with fee breakdown
        """
        logger.info(f"Calculating fees for {document_type} in {uf}")
        
        # Get fee rules
        query = FeeRule.objects.filter(
            uf=uf,
            document_type=document_type,
            is_active=True
        )
        
        if tenant:
            query = query.filter(tenant=tenant)
        
        # Order by version descending to get latest
        rules = query.order_by('-version', '-effective_date')
        
        fees = {
            "emolumentos": Decimal('0.00'),
            "frj": Decimal('0.00'),
            "fundo_estadual": Decimal('0.00'),
            "itbi": Decimal('0.00'),
            "total": Decimal('0.00')
        }
        
        # Group by fee_type and get latest version
        fee_types_processed = set()
        for rule in rules:
            if rule.fee_type not in fee_types_processed:
                fee_types_processed.add(rule.fee_type)
                
                # Calculate fee value
                if rule.fee_type in ["emolumentos", "frj", "fundo_estadual"]:
                    # Fixed fee
                    fees[rule.fee_type] = rule.value
                elif rule.fee_type == "itbi" and base_value:
                    # Percentage of base value
                    fees["itbi"] = base_value * (rule.value / Decimal('100'))
                else:
                    fees[rule.fee_type] = rule.value
        
        fees["total"] = sum(fees.values())
        
        return fees

