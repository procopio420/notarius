from rest_framework import permissions, viewsets, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes, authentication_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from django.db.models import Q

from apps.base.views import BaseTenantViewSet as BaseTenantViewSetBase

from .models import Tenant, RegistryRequest
from .serializers import TenantSerializer, TenantSearchSerializer, RegistryRequestSerializer


class TenantViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Tenants são geridos via admin; expor somente leitura.
    """

    queryset = Tenant.objects.all().order_by("nome")
    serializer_class = TenantSerializer
    permission_classes = [permissions.IsAuthenticated]


class BaseTenantViewSet(BaseTenantViewSetBase):
    """Inherits tenant resolution (including default_tenant fallback) from apps.base.views."""

    pass


class SearchThrottle(AnonRateThrottle):
    """Throttle for tenant search endpoint"""
    rate = '60/min'


@api_view(['GET'])
@throttle_classes([SearchThrottle])
@authentication_classes([])  # Disable authentication - must be before permission_classes
@permission_classes([permissions.AllowAny])  # Allow unauthenticated access
def tenant_search_view(request):
    """
    Search tenants (cartórios) by name or municipio.
    Query params: q (search term), uf (optional filter), limit (default 20)
    """
    search_term = request.query_params.get('q', '').strip()
    uf_filter = request.query_params.get('uf', '').strip().upper()
    
    try:
        limit = int(request.query_params.get('limit', 20))
    except (ValueError, TypeError):
        limit = 20
    
    # Limit max results to prevent abuse
    limit = min(limit, 50)
    
    queryset = Tenant.objects.all()
    
    # Apply search filter
    if search_term:
        queryset = queryset.filter(
            Q(nome__icontains=search_term) | Q(municipio__icontains=search_term)
        )
    
    # Apply UF filter
    if uf_filter:
        queryset = queryset.filter(uf=uf_filter)
    
    # Order by nome and limit results
    queryset = queryset.order_by('nome')[:limit]
    
    serializer = TenantSearchSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@authentication_classes([])  # Disable authentication - must be before permission_classes
@permission_classes([permissions.AllowAny])  # Allow unauthenticated access
def tenant_request_new_view(request):
    """
    Create a new tenant (cartório) registration request.
    Body: { nome, municipio, uf, note? }
    """
    serializer = RegistryRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    registry_request = serializer.save()
    
    return Response({
        'request_id': str(registry_request.id)
    }, status=status.HTTP_201_CREATED)
