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
    cpf_hash = serializers.CharField(max_length=64, required=False, allow_blank=True)
    phone_hash = serializers.CharField(max_length=64, required=False, allow_blank=True)
    cartorio_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'confirm_password', 
                 'first_name', 'last_name', 'cpf_hash', 'phone_hash', 'cartorio_id')

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

    def validate_cpf_hash(self, value):
        """Validate that cpf_hash is a valid SHA256 hex string (64 chars)"""
        if value and len(value) != 64:
            raise serializers.ValidationError("cpf_hash must be a 64-character hex string (SHA256)")
        if value:
            try:
                int(value, 16)  # Check if it's valid hex
            except ValueError:
                raise serializers.ValidationError("cpf_hash must be a valid hex string")
        return value

    def validate_phone_hash(self, value):
        """Validate that phone_hash is a valid SHA256 hex string (64 chars)"""
        if value and len(value) != 64:
            raise serializers.ValidationError("phone_hash must be a 64-character hex string (SHA256)")
        if value:
            try:
                int(value, 16)  # Check if it's valid hex
            except ValueError:
                raise serializers.ValidationError("phone_hash must be a valid hex string")
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        cpf_hash = validated_data.pop('cpf_hash', None)
        phone_hash = validated_data.pop('phone_hash', None)
        cartorio_id = validated_data.pop('cartorio_id', None)
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=password,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        
        # Store hashed CPF/phone in profile if needed (for future use)
        # For now, we don't store them as per requirements
        
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
