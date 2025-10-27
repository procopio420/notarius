"""
Analytics views for Notarius.

This module contains viewsets for analytics and TRELLIS functionality.
"""

from django.contrib.auth.models import User
from django_filters import rest_framework as df_filters
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.base.views import BaseTenantViewSet

from .models import AIUsageAnalytics, TRELLISInteractionLog, TRELLISClusterMetrics
from .serializers import AIUsageAnalyticsSerializer, TRELLISInteractionLogSerializer, TRELLISClusterMetricsSerializer


class AIUsageAnalyticsViewSet(BaseTenantViewSet):
    """ViewSet for AI usage analytics."""
    
    queryset = AIUsageAnalytics.objects.all().order_by("-created_at")
    serializer_class = AIUsageAnalyticsSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["service_name", "operation_type", "status"]
    search_fields = ["service_name", "operation_type"]
    ordering_fields = ["created_at", "response_time_ms", "tokens_used"]

    def perform_create(self, serializer):
        tenant = self._require_tenant()
        serializer.save(tenant=tenant, user=self.request.user)