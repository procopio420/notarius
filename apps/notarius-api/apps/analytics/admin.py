from django.contrib import admin
from apps.base.admin_mixins import BaseTenantAdmin
from .models import AIUsageAnalytics, TRELLISInteractionLog, TRELLISClusterMetrics


@admin.register(AIUsageAnalytics)
class AIUsageAnalyticsAdmin(BaseTenantAdmin):
    list_display = ['date', 'total_generations', 'successful_generations', 'average_confidence', 'tenant']
    list_filter = ['date', 'tenant']
    search_fields = ['tenant__nome']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Período', {
            'fields': ('tenant', 'date')
        }),
        ('Gerações', {
            'fields': ('total_generations', 'successful_generations', 'failed_generations')
        }),
        ('Métricas', {
            'fields': ('average_confidence', 'average_generation_time_ms')
        }),
        ('Mais Usados', {
            'fields': ('most_used_templates', 'most_used_clauses'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TRELLISInteractionLog)
class TRELLISInteractionLogAdmin(BaseTenantAdmin):
    list_display = ['interaction_id', 'user', 'matched_cluster', 'success', 'created_at']
    list_filter = ['success', 'matched_cluster', 'used_llm_fallback', 'created_at']
    search_fields = ['original_command', 'user__username']
    readonly_fields = ['interaction_id', 'created_at']
    
    fieldsets = (
        ('Interação', {
            'fields': ('user', 'session_id', 'original_command', 'parsed_intent')
        }),
        ('Classificação TRELLIS', {
            'fields': ('matched_cluster', 'cluster_confidence', 'used_deterministic_parser', 'used_llm_fallback')
        }),
        ('Feedback do Usuário', {
            'fields': ('user_accepted', 'user_edited', 'user_regenerated', 'sentiment_score', 'user_feedback_text')
        }),
        ('Métricas de Performance', {
            'fields': ('processing_time_ms', 'llm_tokens_used', 'llm_cost_usd')
        }),
        ('Resultado', {
            'fields': ('success', 'error_type', 'error_message')
        }),
    )


@admin.register(TRELLISClusterMetrics)
class TRELLISClusterMetricsAdmin(BaseTenantAdmin):
    list_display = ['cluster_id', 'cluster_name', 'priority_score', 'success_rate', 'total_interactions']
    list_filter = ['is_active', 'needs_refinement']
    ordering = ['-priority_score']
    
    fieldsets = (
        ('Cluster', {
            'fields': ('cluster_id', 'cluster_name', 'is_active', 'needs_refinement')
        }),
        ('Volume', {
            'fields': ('total_interactions', 'interactions_last_7_days', 'interactions_last_30_days')
        }),
        ('Sentimento', {
            'fields': ('avg_sentiment', 'negative_sentiment_count', 'positive_sentiment_count')
        }),
        ('Performance', {
            'fields': ('success_rate', 'avg_confidence', 'user_acceptance_rate', 'user_edit_rate', 'avg_processing_time_ms')
        }),
        ('Priorização', {
            'fields': ('strategic_priority', 'revenue_impact', 'priority_score')
        }),
    )
