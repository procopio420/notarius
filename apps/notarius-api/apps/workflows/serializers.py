from rest_framework import serializers
from .models import WorkflowTask, DocumentoNota, NotificationTemplate, NotificationLog


class WorkflowTaskSerializer(serializers.ModelSerializer):
    """Serializer for WorkflowTask model."""
    
    class Meta:
        model = WorkflowTask
        fields = [
            'id',
            'titulo',
            'descricao',
            'tipo',
            'prioridade',
            'status',
            'assigned_to',
            'created_by',
            'deadline',
            'started_at',
            'completed_at',
            'documento',
            'minuta',
            'processo',
            'metadata',
            'notes',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DocumentoNotaSerializer(serializers.ModelSerializer):
    """Serializer for DocumentoNota model."""
    
    class Meta:
        model = DocumentoNota
        fields = [
            'id',
            'documento',
            'titulo',
            'conteudo',
            'is_private',
            'is_resolved',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for NotificationTemplate model."""
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id',
            'nome',
            'tipo',
            'trigger',
            'assunto',
            'corpo',
            'is_active',
            'variables',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for NotificationLog model."""
    
    class Meta:
        model = NotificationLog
        fields = [
            'id',
            'template',
            'recipient_name',
            'recipient_email',
            'recipient_phone',
            'rendered_subject',
            'rendered_body',
            'status',
            'sent_at',
            'delivered_at',
            'error_message',
            'retry_count',
            'context_data',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
