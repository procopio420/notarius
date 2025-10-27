import uuid
from django.db import models
from django.conf import settings

from apps.base.models import BaseTenantModel


class AIUsageAnalytics(BaseTenantModel):
    """
    Model for tracking AI usage analytics.
    """
    date = models.DateField(help_text="Date of usage")
    total_generations = models.PositiveIntegerField(default=0)
    successful_generations = models.PositiveIntegerField(default=0)
    failed_generations = models.PositiveIntegerField(default=0)
    average_confidence = models.FloatField(default=0.0)
    average_generation_time_ms = models.PositiveIntegerField(default=0)
    most_used_templates = models.JSONField(default=list)
    most_used_clauses = models.JSONField(default=list)
    
    class Meta:
        db_table = 'ai_usage_analytics'
        unique_together = [['tenant', 'date']]
        ordering = ['-date']
    
    def __str__(self):
        return f"AI Analytics {self.date} - {self.tenant.nome}"


class TRELLISInteractionLog(BaseTenantModel):
    """Track every user interaction for TRELLIS clustering analysis."""
    interaction_id = models.UUIDField(default=uuid.uuid4, unique=True)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    session_id = models.CharField(max_length=255)
    
    # User input
    original_command = models.TextField()
    parsed_intent = models.JSONField()  # Structured intent output
    
    # TRELLIS classification
    matched_cluster = models.CharField(max_length=255, null=True, blank=True)
    cluster_confidence = models.FloatField(default=0.0)
    used_deterministic_parser = models.BooleanField(default=False)
    used_llm_fallback = models.BooleanField(default=False)
    
    # User feedback & sentiment
    user_accepted = models.BooleanField(null=True, blank=True)  # Did user accept result?
    user_edited = models.BooleanField(default=False)  # Did user edit output?
    user_regenerated = models.BooleanField(default=False)  # Did user retry?
    sentiment_score = models.FloatField(null=True, blank=True)  # -1 to 1
    user_feedback_text = models.TextField(blank=True)
    
    # Performance metrics
    processing_time_ms = models.IntegerField()
    llm_tokens_used = models.IntegerField(default=0)
    llm_cost_usd = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    
    # Outcome
    success = models.BooleanField()
    error_type = models.CharField(max_length=255, null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trellis_interaction_log'
        indexes = [
            models.Index(fields=['matched_cluster', 'created_at']),
            models.Index(fields=['user', 'session_id']),
            models.Index(fields=['success', 'created_at']),
        ]


class TRELLISClusterMetrics(BaseTenantModel):
    """Aggregate metrics for TRELLIS cluster prioritization."""
    cluster_id = models.CharField(max_length=255, unique=True)
    cluster_name = models.CharField(max_length=255)
    
    # Volume metrics (Step 4: Volume x negative sentiment x achievable delta x strategic relevance)
    total_interactions = models.IntegerField(default=0)
    interactions_last_7_days = models.IntegerField(default=0)
    interactions_last_30_days = models.IntegerField(default=0)
    
    # Sentiment metrics
    avg_sentiment = models.FloatField(default=0.0)
    negative_sentiment_count = models.IntegerField(default=0)
    positive_sentiment_count = models.IntegerField(default=0)
    
    # Performance metrics (achievable delta)
    success_rate = models.FloatField(default=0.0)
    avg_confidence = models.FloatField(default=0.0)
    user_acceptance_rate = models.FloatField(default=0.0)
    user_edit_rate = models.FloatField(default=0.0)
    avg_processing_time_ms = models.IntegerField(default=0)
    
    # Strategic relevance (business impact)
    strategic_priority = models.IntegerField(default=1)  # 1-10 scale, set by business
    revenue_impact = models.CharField(max_length=50, default='medium')  # low/medium/high
    
    # Oleve scoring formula: volume x negative_sentiment x achievable_delta x strategic_relevance
    priority_score = models.FloatField(default=0.0)
    
    # Status
    is_active = models.BooleanField(default=True)
    needs_refinement = models.BooleanField(default=False)
    last_analyzed = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trellis_cluster_metrics'
