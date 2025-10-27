from rest_framework import serializers

from .models import Processo, ProcessoParte, Protocolo


class ProcessoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Processo
        fields = [
            "id",
            "tenant",
            "tipo_ato",
            "status",
            "responsavel",
            "sla_at",
            "metadados",
            "deleted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["tenant", "created_at", "updated_at"]


class ProcessoParteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessoParte
        fields = ["id", "tenant", "processo", "parte", "papel", "created_at", "updated_at"]
        read_only_fields = ["tenant", "created_at", "updated_at"]


class ProtocoloSerializer(serializers.ModelSerializer):
    numero_formatado = serializers.ReadOnlyField()
    
    class Meta:
        model = Protocolo
        fields = [
            "id",
            "tenant",
            "numero",
            "ano",
            "processo",
            "tipo",
            "observacoes",
            "numero_formatado",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["tenant", "numero", "created_at", "updated_at"]
