"""
Serializers for documentos app.
"""

from rest_framework import serializers
from .models import Minuta, Documento
from apps.partes.models import Parte
from apps.processos.models import Processo


class MinutaSerializer(serializers.ModelSerializer):
    """Serializer for Minuta model."""
    
    class Meta:
        model = Minuta
        fields = [
            'id',
            'processo',
            'corpo_md',
            'variaveis_json',
            'status',
            'versao',
            'gerada_por',
            'approved_by',
            'approved_at',
            'finalized_at',
            'citations',
            'grounding_confidence',
            'skeleton_cache_key',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'status', 'versao', 'approved_by', 'approved_at',
            'finalized_at', 'skeleton_cache_key',
            'created_at', 'updated_at'
        ]
    
    def validate_processo(self, value):
        """Validate processo belongs to the same tenant."""
        if value.tenant != self.context['request'].user.tenant:
            raise serializers.ValidationError(
                "Processo must belong to the same tenant"
            )
        return value
    
    def create(self, validated_data):
        """Create new minuta with proper defaults."""
        validated_data['tenant'] = self.context['request'].user.tenant
        validated_data['gerada_por'] = 'usuario'
        validated_data['status'] = 'rascunho'
        validated_data['versao'] = 1
        
        return super().create(validated_data)


class MinutaUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing minutas."""
    
    class Meta:
        model = Minuta
        fields = [
            'corpo_md',
            'variaveis_json',
        ]
    
    def update(self, instance, validated_data):
        """Update minuta and increment version."""
        # Increment version on update
        instance.versao += 1
        
        return super().update(instance, validated_data)


class DocumentoSerializer(serializers.ModelSerializer):
    """Serializer for Documento model."""
    
    class Meta:
        model = Documento
        fields = [
            'id',
            'processo',
            's3_key',
            'hash_sha256',
            'mime',
            'pages',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_processo(self, value):
        """Validate processo belongs to the same tenant."""
        if value.tenant != self.context['request'].user.tenant:
            raise serializers.ValidationError(
                "Processo must belong to the same tenant"
            )
        return value