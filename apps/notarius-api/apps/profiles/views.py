from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model

from .models import UserProfile
from .serializers import UserProfileSerializer, UserProfileUpdateSerializer
from apps.tenancy.models import Tenant

User = get_user_model()


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    User profile management - users can only access their own profile
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only access their own profile
        return UserProfile.objects.filter(user=self.request.user)
    
    def get_object(self):
        # Always return the current user's profile
        profile, created = UserProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer
    
    @action(detail=False, methods=['get'], url_path='my-profile')
    def my_profile(self, request):
        """Get current user's profile"""
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], url_path='set-default-tenant')
    def set_default_tenant(self, request):
        """Set default tenant for current user"""
        profile = self.get_object()
        tenant_id = request.data.get('tenant_id')
        
        if not tenant_id:
            return Response(
                {'error': 'tenant_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            if profile.set_default_tenant(tenant):
                serializer = self.get_serializer(profile)
                return Response(serializer.data)
            else:
                return Response(
                    {'error': 'Tenant not accessible to user'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Tenant.DoesNotExist:
            return Response(
                {'error': 'Tenant not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], url_path='add-tenant')
    def add_tenant(self, request):
        """Add tenant to user's accessible tenants"""
        profile = self.get_object()
        tenant_id = request.data.get('tenant_id')
        
        if not tenant_id:
            return Response(
                {'error': 'tenant_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            profile.tenants.add(tenant)
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except Tenant.DoesNotExist:
            return Response(
                {'error': 'Tenant not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], url_path='remove-tenant')
    def remove_tenant(self, request):
        """Remove tenant from user's accessible tenants"""
        profile = self.get_object()
        tenant_id = request.data.get('tenant_id')
        
        if not tenant_id:
            return Response(
                {'error': 'tenant_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tenant = Tenant.objects.get(id=tenant_id)
            profile.tenants.remove(tenant)
            # If this was the default tenant, clear it
            if profile.default_tenant == tenant:
                profile.default_tenant = None
                profile.save()
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        except Tenant.DoesNotExist:
            return Response(
                {'error': 'Tenant not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
