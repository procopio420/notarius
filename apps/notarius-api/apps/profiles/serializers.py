from rest_framework import serializers
from .models import UserProfile
from apps.tenancy.serializers import TenantSerializer


class UserProfileSerializer(serializers.ModelSerializer):
    tenants = TenantSerializer(many=True, read_only=True)
    default_tenant = TenantSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ["id", "user", "tenants", "default_tenant", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile with tenant assignments"""
    
    class Meta:
        model = UserProfile
        fields = ["tenants", "default_tenant"]
    
    def validate_default_tenant(self, value):
        """Ensure default tenant is in accessible tenants"""
        if value and hasattr(self, 'instance') and self.instance:
            if not self.instance.can_access_tenant(value):
                raise serializers.ValidationError(
                    "Default tenant must be in accessible tenants list"
                )
        return value
