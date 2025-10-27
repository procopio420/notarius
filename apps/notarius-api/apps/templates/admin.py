from django.contrib import admin
from apps.base.admin_mixins import BaseTenantAdmin
from .models import DocumentTemplate, Template


@admin.register(DocumentTemplate)
class DocumentTemplateAdmin(BaseTenantAdmin):
    list_display = ['name', 'document_type', 'version', 'is_default', 'is_active', 'created_by', 'created_at']
    list_filter = ['document_type', 'is_default', 'is_active', 'created_at']
    search_fields = ['name', 'document_type', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tenant', 'name', 'document_type', 'version', 'is_default', 'is_active')
        }),
        ('Template', {
            'fields': ('template_path', 'description'),
        }),
        ('Customização', {
            'fields': ('custom_css', 'custom_js', 'custom_fields'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Template)
class TemplateAdmin(BaseTenantAdmin):
    list_display = ['name', 'document_type', 'source', 'is_active', 'usage_count', 'created_at']
    list_filter = ['document_type', 'source', 'is_active', 'created_at']
    search_fields = ['name', 'document_type', 'description']
    readonly_fields = ['usage_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('tenant', 'name', 'document_type', 'version', 'is_active')
        }),
        ('Template', {
            'fields': ('corpo_template', 'schema', 'description'),
        }),
        ('Sistema Híbrido', {
            'fields': ('source', 'jurisdiction', 'usage_count', 'quality_score'),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
