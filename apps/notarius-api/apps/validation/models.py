"""
Validation models.
"""

from django.db import models
from apps.base.models import BaseTenantModel


class ValidationResult(BaseTenantModel):
    """Model for storing validation results."""
    
    document_type = models.CharField(max_length=100, db_index=True)
    extracted_data = models.JSONField(default=dict)
    exigencias = models.JSONField(default=list, help_text="Required items")
    bloqueantes = models.JSONField(default=list, help_text="Blocking issues")
    opcionais = models.JSONField(default=list, help_text="Optional items")
    citacoes = models.JSONField(default=list, help_text="Citations")
    uf = models.CharField(max_length=2, null=True, blank=True)
    validation_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "validation_results"
        indexes = [
            models.Index(fields=["tenant", "document_type"]),
            models.Index(fields=["tenant", "validation_date"]),
        ]

