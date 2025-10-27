from rest_framework import filters, permissions, viewsets

from apps.tenancy.tenancy import get_current_tenant

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["resource_type", "resource_id", "actor__email"]
    ordering = ["-ts"]

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None) or get_current_tenant()
        qs = AuditLog.objects.all()
        if tenant:
            qs = qs.filter(tenant=tenant)
        return qs
