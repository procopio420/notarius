"""
Validation serializers.
"""

from rest_framework import serializers
from .models import ValidationResult


class ValidationResultSerializer(serializers.ModelSerializer):
    """Serializer for ValidationResult."""
    
    class Meta:
        model = ValidationResult
        fields = [
            'id', 'document_type', 'extracted_data',
            'exigencias', 'bloqueantes', 'opcionais', 'citacoes',
            'uf', 'validation_date'
        ]
        read_only_fields = ['id', 'validation_date']

