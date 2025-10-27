import uuid
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

from apps.base.models import BaseTenantModel


class DocumentTemplate(BaseTenantModel):
    """
    Template for document generation with tenant customization support.
    """
    name = models.CharField(max_length=100, help_text="Template name (e.g., 'procuracao', 'certidao')")
    document_type = models.CharField(max_length=50, help_text="Type of document (procuracao, certidao, testamento, etc.)")
    template_path = models.CharField(max_length=255, help_text="Path to template file")
    is_default = models.BooleanField(default=False, help_text="Is this a default template?")
    is_active = models.BooleanField(default=True, help_text="Is this template active?")
    version = models.CharField(max_length=20, default="1.0", help_text="Template version")
    
    # Template customization
    custom_css = models.TextField(blank=True, help_text="Custom CSS for this template")
    custom_js = models.TextField(blank=True, help_text="Custom JavaScript for this template")
    custom_fields = models.JSONField(default=dict, blank=True, help_text="Custom fields for this template")
    
    # Metadata
    description = models.TextField(blank=True, help_text="Template description")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_templates")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="updated_templates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "document_templates"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "name"], name="uq_template_tenant_name"),
        ]
        indexes = [
            models.Index(fields=["tenant", "document_type"], name="ix_template_tenant_type"),
            models.Index(fields=["tenant", "is_default"], name="ix_template_tenant_default"),
            models.Index(fields=["tenant", "is_active"], name="ix_template_tenant_active"),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.document_type}) - {self.tenant.nome}"
    
    @classmethod
    def get_default_template(cls, document_type: str) -> "DocumentTemplate":
        """Get the default template for a document type."""
        return cls.objects.filter(
            document_type=document_type,
            is_default=True,
            is_active=True
        ).first()
    
    @classmethod
    def get_tenant_template(cls, tenant, document_type: str) -> "DocumentTemplate":
        """Get the tenant-specific template for a document type, fallback to default."""
        # Try to get tenant-specific template first
        template = cls.objects.filter(
            tenant=tenant,
            document_type=document_type,
            is_active=True
        ).first()
        
        # Fallback to default template if no tenant-specific template
        if not template:
            template = cls.get_default_template(document_type)
        
        return template
    
    def get_template_path(self) -> str:
        """Get the full template path."""
        if self.template_path.startswith('/'):
            return self.template_path
        return f"templates/{self.template_path}"
    
    def get_custom_fields(self) -> dict:
        """Get custom fields for this template."""
        return self.custom_fields or {}
    
    def get_custom_css(self) -> str:
        """Get custom CSS for this template."""
        return self.custom_css or ""
    
    def get_custom_js(self) -> str:
        """Get custom JavaScript for this template."""
        return self.custom_js or ""


class Template(BaseTenantModel):
    """
    Template for document content generation with Jinja2 support.
    """
    name = models.CharField(max_length=100, help_text="Template name")
    document_type = models.CharField(max_length=50, help_text="Type of document")
    corpo_template = models.TextField(help_text="Template content with Jinja2 syntax")
    schema = models.JSONField(default=dict, help_text="Template variable schema")
    is_active = models.BooleanField(default=True, help_text="Is this template active?")
    version = models.CharField(max_length=20, default="1.0", help_text="Template version")
    
    # New fields for hybrid template system
    source = models.CharField(
        max_length=20, 
        choices=[("tenant", "Tenant"), ("lexnode", "LexNode"), ("ai_generated", "AI Generated")],
        default="tenant",
        help_text="Source of this template"
    )
    jurisdiction = models.CharField(
        max_length=10, 
        blank=True, 
        help_text="Legal jurisdiction (for lexnode templates)"
    )
    usage_count = models.PositiveIntegerField(
        default=0, 
        help_text="Number of times this template has been used"
    )
    quality_score = models.FloatField(
        null=True, 
        blank=True, 
        help_text="User feedback quality score (0.0 to 1.0)"
    )
    
    # Metadata
    description = models.TextField(blank=True, help_text="Template description")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_content_templates")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="updated_content_templates")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "templates"
        constraints = [
            models.UniqueConstraint(fields=["tenant", "name"], name="uq_template_content_name"),
        ]
        indexes = [
            models.Index(fields=["tenant", "document_type"], name="ix_template_content_type"),
            models.Index(fields=["tenant", "is_active"], name="ix_template_content_active"),
            models.Index(fields=["tenant", "source"], name="ix_template_content_source"),
            models.Index(fields=["tenant", "jurisdiction"], name="ix_template_jurisdiction"),
            models.Index(fields=["usage_count"], name="ix_template_content_usage"),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.document_type}) - {self.tenant.nome}"
