from rest_framework import serializers
from .models import AIUsageAnalytics, TRELLISInteractionLog, TRELLISClusterMetrics


class AIUsageAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for AIUsageAnalytics model."""
    
    class Meta:
        model = AIUsageAnalytics
        fields = [
            'id',
            'date',
            'total_generations',
            'successful_generations',
            'failed_generations',
            'average_confidence',
            'average_generation_time_ms',
            'most_used_templates',
            'most_used_clauses',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TRELLISInteractionLogSerializer(serializers.ModelSerializer):
    """Serializer for TRELLISInteractionLog model."""
    
    class Meta:
        model = TRELLISInteractionLog
        fields = [
            'id',
            'interaction_id',
            'user',
            'session_id',
            'original_command',
            'parsed_intent',
            'matched_cluster',
            'cluster_confidence',
            'used_deterministic_parser',
            'used_llm_fallback',
            'user_accepted',
            'user_edited',
            'user_regenerated',
            'sentiment_score',
            'user_feedback_text',
            'processing_time_ms',
            'llm_tokens_used',
            'llm_cost_usd',
            'success',
            'error_type',
            'error_message',
            'created_at',
        ]
        read_only_fields = ['id', 'interaction_id', 'created_at']


class TRELLISClusterMetricsSerializer(serializers.ModelSerializer):
    """Serializer for TRELLISClusterMetrics model."""
    
    class Meta:
        model = TRELLISClusterMetrics
        fields = [
            'id',
            'cluster_id',
            'cluster_name',
            'total_interactions',
            'interactions_last_7_days',
            'interactions_last_30_days',
            'avg_sentiment',
            'negative_sentiment_count',
            'positive_sentiment_count',
            'success_rate',
            'avg_confidence',
            'user_acceptance_rate',
            'user_edit_rate',
            'avg_processing_time_ms',
            'strategic_priority',
            'revenue_impact',
            'priority_score',
            'is_active',
            'needs_refinement',
            'last_analyzed',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'priority_score', 'last_analyzed', 'created_at', 'updated_at']
