from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.conf import settings

from .serializers import LoginSerializer, RegisterSerializer, UserSerializer, UserTenantAssociationSerializer
from apps.tenancy.models import Tenant
from apps.auditoria.models import AuditLog

User = get_user_model()


@api_view(['POST'])
@authentication_classes([])  # Disable authentication - don't check tokens on login
@permission_classes([AllowAny])
def login_view(request):
    """Login endpoint"""
    serializer = LoginSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    user = authenticate(username=username, password=password)
    
    if user is None:
        return Response(
            {'detail': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'detail': 'Account is disabled'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    # Get or create token
    token, created = Token.objects.get_or_create(user=user)
    
    # Get user data with tenant information
    user_data = UserSerializer(user).data
    
    # Set default tenant in localStorage if user has a default tenant
    default_tenant = None
    if hasattr(user, 'profile') and user.profile.default_tenant:
        default_tenant = user.profile.default_tenant
    
    return Response({
        'token': token.key,
        'user': user_data,
        'default_tenant': default_tenant.id if default_tenant else None
    })


class RegisterThrottle(AnonRateThrottle):
    """Throttle for registration endpoint - allows more registrations in development"""
    rate = '100/hour' if settings.DEBUG else '10/hour'


@api_view(['POST'])
@authentication_classes([])  # Disable authentication - don't check tokens on register
@permission_classes([AllowAny])
@throttle_classes([RegisterThrottle])
def register_view(request):
    """Register endpoint with cartório (tenant) support"""
    serializer = RegisterSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Extract cartorio_id before creating user
        cartorio_id = serializer.validated_data.get('cartorio_id')
        email = serializer.validated_data['email']
        
        # Create user
        user = serializer.save()
        
        # Handle tenant membership
        if cartorio_id:
            try:
                tenant = Tenant.objects.get(id=cartorio_id)
                # Add tenant to user's accessible tenants
                user.profile.tenants.add(tenant)
                # Set as default tenant
                user.profile.default_tenant = tenant
                user.profile.save()
                
                # Create audit log for registration with tenant
                try:
                    AuditLog.objects.create(
                        tenant=tenant,
                        actor=user,
                        resource_type="user",
                        resource_id=user.id,
                        action="register",
                        ip=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        extra={
                            'email': email,
                            'cartorio_id': str(cartorio_id),
                        }
                    )
                except Exception:
                    # If audit log fails, don't fail registration
                    pass
                
                # Create token for the new user
                token, created = Token.objects.get_or_create(user=user)
                
                return Response({
                    'status': 'ACTIVE',
                    'redirect': '/inbox',
                    'token': token.key,
                    'user': UserSerializer(user).data,
                }, status=status.HTTP_201_CREATED)
            except Tenant.DoesNotExist:
                return Response(
                    {'detail': 'Cartório not found'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # No tenant selected - user requested new cartório
            # Create token for the new user
            token, created = Token.objects.get_or_create(user=user)
            
            return Response({
                'status': 'NO_CARTORIO',
                'redirect': '/onboarding/pending-cartorio',
                'token': token.key,
                'user': UserSerializer(user).data,
            }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response(
            {'detail': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout endpoint"""
    try:
        # Delete the token
        request.user.auth_token.delete()
        return Response({'detail': 'Successfully logged out'})
    except:
        return Response({'detail': 'Successfully logged out'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Get current user info"""
    return Response({
        'user': UserSerializer(request.user).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_tenants_view(request):
    """Get user's accessible tenants"""
    if not hasattr(request.user, 'profile'):
        return Response({'tenants': []})
    
    tenants = request.user.profile.get_accessible_tenants()
    return Response({
        'tenants': [
            {
                'id': tenant.id,
                'nome': tenant.nome,
                'uf': tenant.uf,
                'is_default': tenant.id == request.user.profile.default_tenant.id if request.user.profile.default_tenant else False
            }
            for tenant in tenants
        ]
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_default_tenant_view(request):
    """Set default tenant for the current user"""
    tenant_id = request.data.get('tenant_id')
    
    if not tenant_id:
        return Response(
            {'detail': 'tenant_id is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        return Response(
            {'detail': 'Tenant not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if not hasattr(request.user, 'profile'):
        return Response(
            {'detail': 'User profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    if not request.user.profile.can_access_tenant(tenant):
        return Response(
            {'detail': 'You do not have access to this tenant'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    request.user.profile.set_default_tenant(tenant)
    
    return Response({
        'detail': 'Default tenant updated successfully',
        'default_tenant': {
            'id': tenant.id,
            'nome': tenant.nome,
            'uf': tenant.uf
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def manage_user_tenants_view(request):
    """Manage user-tenant associations (admin only)"""
    if not request.user.is_staff:
        return Response(
            {'detail': 'Permission denied'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    user_id = request.data.get('user_id')
    if not user_id:
        return Response(
            {'detail': 'user_id is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'detail': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = UserTenantAssociationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # Update user's tenant associations
    if not hasattr(target_user, 'profile'):
        return Response(
            {'detail': 'User profile not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    
    tenant_ids = serializer.validated_data['tenant_ids']
    default_tenant_id = serializer.validated_data.get('default_tenant_id')
    
    # Update accessible tenants
    tenants = Tenant.objects.filter(id__in=tenant_ids)
    target_user.profile.tenants.set(tenants)
    
    # Update default tenant
    if default_tenant_id:
        default_tenant = Tenant.objects.get(id=default_tenant_id)
        target_user.profile.default_tenant = default_tenant
    else:
        target_user.profile.default_tenant = None
    
    target_user.profile.save()
    
    return Response({
        'detail': 'User tenant associations updated successfully',
        'user': UserSerializer(target_user).data
    })
