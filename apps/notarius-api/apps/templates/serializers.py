from rest_framework import serializers
from .models import DocumentTemplate, Template


class DocumentTemplateSerializer(serializers.ModelSerializer):
    """Serializer for DocumentTemplate model."""
    
    class Meta:
        model = DocumentTemplate
        fields = [
            'id',
            'name',
            'document_type',
            'template_path',
            'is_default',
            'is_active',
            'version',
            'custom_css',
            'custom_js',
            'custom_fields',
            'description',
            'created_by',
            'updated_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate template name is unique within tenant."""
        if self.instance:
            # Update case
            if DocumentTemplate.objects.filter(
                tenant=self.instance.tenant,
                name=value
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Template name must be unique within tenant"
                )
        else:
            # Create case
            if DocumentTemplate.objects.filter(
                tenant=self.context['request'].user.tenant,
                name=value
            ).exists():
                raise serializers.ValidationError(
                    "Template name must be unique within tenant"
                )
        return value
    
    def validate_document_type(self, value):
        """Validate document type is one of the allowed values."""
        allowed_types = [
            'procuracao', 'certidao', 'testamento', 
            'escritura', 'contrato', 'documento'
        ]
        if value not in allowed_types:
            raise serializers.ValidationError(
                f"Document type must be one of: {', '.join(allowed_types)}"
            )
        return value


class TemplateSerializer(serializers.ModelSerializer):
    """Serializer for Template model."""
    
    class Meta:
        model = Template
        fields = [
            'id',
            'name',
            'document_type',
            'corpo_template',
            'schema',
            'is_active',
            'version',
            'source',
            'jurisdiction',
            'usage_count',
            'quality_score',
            'description',
            'created_by',
            'updated_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate template name is unique within tenant."""
        if self.instance:
            # Update case
            if Template.objects.filter(
                tenant=self.instance.tenant,
                name=value
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "Template name must be unique within tenant"
                )
        else:
            # Create case
            if Template.objects.filter(
                tenant=self.context['request'].user.tenant,
                name=value
            ).exists():
                raise serializers.ValidationError(
                    "Template name must be unique within tenant"
                )
        return value
