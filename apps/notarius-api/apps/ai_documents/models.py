from django.db import models
from django.conf import settings

from apps.base.models import BaseTenantModel


class AIGeneratedMinuta(BaseTenantModel):
    """
    Model for tracking AI-generated minutas with metadata.
    """
    minuta = models.ForeignKey('documentos.Minuta', on_delete=models.CASCADE, related_name='ai_generations')
    original_command = models.TextField(help_text="Original user command")
    parsed_intent = models.JSONField(help_text="Parsed intent from AI")
    ai_model_version = models.CharField(max_length=50, help_text="AI model version used")
    confidence_score = models.FloatField(help_text="Confidence score (0.0 to 1.0)")
    generation_time_ms = models.PositiveIntegerField(help_text="Generation time in milliseconds")
    clauses_used = models.JSONField(default=list, help_text="List of clause IDs used")
    template_source = models.CharField(
        max_length=20,
        choices=[("tenant", "Tenant"), ("lexnode", "LexNode"), ("ai_generated", "AI Generated")],
        default="ai_generated",
        help_text="Source of the template used"
    )
    generation_timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_generated_minutas'
        ordering = ['-generation_timestamp']
        indexes = [
            models.Index(fields=["tenant", "generation_timestamp"], name="ix_ai_generated_timestamp"),
            models.Index(fields=["tenant", "template_source"], name="ix_ai_generated_source"),
            models.Index(fields=["confidence_score"], name="ix_ai_generated_confidence"),
        ]
    
    def __str__(self):
        return f"AI Generation {self.id} - {self.minuta.id}"
