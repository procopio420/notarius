from rest_framework import serializers
from .models import AIGeneratedMinuta


class AIGeneratedMinutaSerializer(serializers.ModelSerializer):
    """Serializer for AIGeneratedMinuta model."""
    
    class Meta:
        model = AIGeneratedMinuta
        fields = [
            'id',
            'minuta',
            'original_command',
            'parsed_intent',
            'ai_model_version',
            'confidence_score',
            'generation_time_ms',
            'clauses_used',
            'template_source',
            'generation_timestamp',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'generation_timestamp', 'created_at', 'updated_at']
