from rest_framework import serializers
from .models import Tenant, RegistryRequest


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "nome", "uf", "municipio", "tipo", "settings", "created_at", "updated_at"]
        read_only_fields = fields


class TenantSearchSerializer(serializers.ModelSerializer):
    """Serializer for tenant search results"""
    class Meta:
        model = Tenant
        fields = ["id", "nome", "municipio", "uf", "tipo"]
        read_only_fields = fields


class RegistryRequestSerializer(serializers.ModelSerializer):
    """Serializer for tenant registration requests"""
    class Meta:
        model = RegistryRequest
        fields = ["id", "nome", "municipio", "uf", "note"]
        read_only_fields = ["id"]
