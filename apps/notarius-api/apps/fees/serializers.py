"""
Fee serializers.
"""

from rest_framework import serializers
from .models import FeeRule


class FeeRuleSerializer(serializers.ModelSerializer):
    """Serializer for FeeRule."""
    
    class Meta:
        model = FeeRule
        fields = [
            'id', 'uf', 'document_type', 'fee_type', 'value',
            'version', 'effective_date', 'is_active'
        ]
        read_only_fields = ['id']


class FeeCalculationSerializer(serializers.Serializer):
    """Serializer for fee calculation response."""
    emolumentos = serializers.DecimalField(max_digits=10, decimal_places=2)
    frj = serializers.DecimalField(max_digits=10, decimal_places=2)
    fundo_estadual = serializers.DecimalField(max_digits=10, decimal_places=2)
    itbi = serializers.DecimalField(max_digits=10, decimal_places=2)
    total = serializers.DecimalField(max_digits=10, decimal_places=2)

