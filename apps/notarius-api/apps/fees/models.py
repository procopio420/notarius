"""
Fee models.
"""

from django.db import models
from apps.base.models import BaseTenantModel


class FeeRule(BaseTenantModel):
    """Model for fee rules by UF and document type."""
    
    uf = models.CharField(max_length=2, db_index=True)
    document_type = models.CharField(max_length=100, db_index=True)
    fee_type = models.CharField(max_length=50, db_index=True)  # "emolumentos", "frj", "fundo_estadual", "itbi"
    value = models.DecimalField(max_digits=10, decimal_places=2)
    version = models.CharField(max_length=20, default="2024.1")
    effective_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        db_table = "fee_rules"
        indexes = [
            models.Index(fields=["tenant", "uf", "document_type"]),
            models.Index(fields=["uf", "document_type", "fee_type", "is_active"]),
        ]
        unique_together = [["uf", "document_type", "fee_type", "version"]]

