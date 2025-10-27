from django.contrib import admin
from apps.base.admin_mixins import BaseTenantAdmin
from .models import WorkflowTask, DocumentoNota, NotificationTemplate, NotificationLog


@admin.register(WorkflowTask)
class WorkflowTaskAdmin(BaseTenantAdmin):
    list_display = ['titulo', 'tipo', 'status', 'prioridade', 'assigned_to', 'deadline', 'created_at']
    list_filter = ['tipo', 'status', 'prioridade', 'created_at']
    search_fields = ['titulo', 'descricao']
    autocomplete_fields = ['assigned_to', 'created_by', 'documento', 'minuta', 'processo']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('titulo', 'descricao', 'tipo', 'prioridade', 'status')
        }),
        ('Atribuição', {
            'fields': ('assigned_to', 'created_by', 'deadline')
        }),
        ('Timing', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Objetos Relacionados', {
            'fields': ('documento', 'minuta', 'processo'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('metadata', 'notes', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DocumentoNota)
class DocumentoNotaAdmin(BaseTenantAdmin):
    list_display = ['titulo', 'documento', 'is_private', 'is_resolved', 'created_by', 'created_at']
    list_filter = ['is_private', 'is_resolved', 'created_at']
    search_fields = ['titulo', 'conteudo']
    autocomplete_fields = ['documento', 'created_by']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Nota', {
            'fields': ('documento', 'titulo', 'conteudo')
        }),
        ('Configurações', {
            'fields': ('is_private', 'is_resolved')
        }),
        ('Metadados', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(BaseTenantAdmin):
    list_display = ['nome', 'tipo', 'trigger', 'is_active', 'created_by', 'created_at']
    list_filter = ['tipo', 'trigger', 'is_active', 'created_at']
    search_fields = ['nome', 'assunto']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Template', {
            'fields': ('nome', 'tipo', 'trigger', 'is_active')
        }),
        ('Conteúdo', {
            'fields': ('assunto', 'corpo', 'variables')
        }),
        ('Metadados', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(BaseTenantAdmin):
    list_display = ['template', 'recipient_email', 'status', 'sent_at', 'created_at']
    list_filter = ['status', 'sent_at', 'created_at']
    search_fields = ['recipient_email', 'recipient_name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Notificação', {
            'fields': ('template', 'status', 'sent_at', 'delivered_at')
        }),
        ('Destinatário', {
            'fields': ('recipient_name', 'recipient_email', 'recipient_phone')
        }),
        ('Conteúdo', {
            'fields': ('rendered_subject', 'rendered_body'),
            'classes': ('collapse',)
        }),
        ('Erros', {
            'fields': ('error_message', 'retry_count'),
            'classes': ('collapse',)
        }),
        ('Contexto', {
            'fields': ('context_data',),
            'classes': ('collapse',)
        }),
    )
