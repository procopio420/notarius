from rest_framework import serializers

from .models import Parte


class ParteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parte
        fields = [
            "id",
            "tenant",
            "tipo",
            "nome",
            "nome_normalizado",
            "cpf_hash",
            "cnpj_hash",
            "dados_cript",
            "contatos",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "tenant",
            "nome_normalizado",
            "cpf_hash",
            "cnpj_hash",
            "created_at",
            "updated_at",
        ]
