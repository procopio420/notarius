from rest_framework import serializers
from .models import Tenant


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "nome", "uf", "settings", "created_at", "updated_at"]
        read_only_fields = fields
