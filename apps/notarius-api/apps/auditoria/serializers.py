from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "tenant",
            "actor",
            "actor_email",
            "resource_type",
            "resource_id",
            "action",
            "ip",
            "user_agent",
            "ts",
            "diff_json",
            "extra",
        ]
        read_only_fields = fields
