from django.contrib import admin
from apps.base.admin_mixins import BaseTenantAdmin
from .models import AIGeneratedMinuta


@admin.register(AIGeneratedMinuta)
class AIGeneratedMinutaAdmin(BaseTenantAdmin):
    list_display = ['id', 'minuta', 'ai_model_version', 'confidence_score', 'template_source', 'generation_timestamp']
    list_filter = ['ai_model_version', 'template_source', 'generation_timestamp']
    search_fields = ['original_command', 'minuta__id']
    readonly_fields = ['generation_timestamp', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Geração', {
            'fields': ('minuta', 'original_command', 'parsed_intent', 'ai_model_version')
        }),
        ('Métricas', {
            'fields': ('confidence_score', 'generation_time_ms', 'template_source')
        }),
        ('Cláusulas', {
            'fields': ('clauses_used',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('generation_timestamp', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
