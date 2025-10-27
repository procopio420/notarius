from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.tenancy.models import Tenant

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    cpf = serializers.CharField(max_length=14)
    phone = serializers.CharField(max_length=20)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password', 
                 'first_name', 'last_name', 'cpf', 'phone')

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        
        # Store additional fields in user profile if needed
        # For now, we'll just create the basic user
        
        return user


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ('id', 'nome', 'uf')


class UserSerializer(serializers.ModelSerializer):
    tenants = serializers.SerializerMethodField()
    default_tenant = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'is_staff', 'is_superuser', 'date_joined', 'tenants', 'default_tenant')
        read_only_fields = ('id', 'date_joined')
    
    def get_tenants(self, obj):
        """Get accessible tenants for the user"""
        if hasattr(obj, 'profile'):
            return TenantSerializer(obj.profile.get_accessible_tenants(), many=True).data
        return []
    
    def get_default_tenant(self, obj):
        """Get default tenant for the user"""
        if hasattr(obj, 'profile') and obj.profile.default_tenant:
            return TenantSerializer(obj.profile.default_tenant).data
        return None


class UserTenantAssociationSerializer(serializers.Serializer):
    """Serializer for managing user-tenant associations"""
    tenant_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        help_text="List of tenant IDs to associate with the user"
    )
    default_tenant_id = serializers.UUIDField(
        required=False,
        write_only=True,
        help_text="ID of the default tenant"
    )
    
    def validate_tenant_ids(self, value):
        """Validate that all tenant IDs exist"""
        existing_tenants = Tenant.objects.filter(id__in=value)
        if len(existing_tenants) != len(value):
            raise serializers.ValidationError("One or more tenant IDs are invalid")
        return value
    
    def validate_default_tenant_id(self, value):
        """Validate that default tenant ID exists"""
        if value:
            try:
                Tenant.objects.get(id=value)
            except Tenant.DoesNotExist:
                raise serializers.ValidationError("Default tenant ID is invalid")
        return value
    
    def validate(self, attrs):
        """Validate that default tenant is in the tenant list"""
        tenant_ids = attrs.get('tenant_ids', [])
        default_tenant_id = attrs.get('default_tenant_id')
        
        if default_tenant_id and default_tenant_id not in tenant_ids:
            raise serializers.ValidationError(
                "Default tenant must be in the list of accessible tenants"
            )
        return attrs
