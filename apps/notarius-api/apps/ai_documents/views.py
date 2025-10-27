"""
AI Documents views for Notarius.

This module contains viewsets for AI-generated documents and related functionality.
"""

import asyncio
from django.contrib.auth.models import User
from django_filters import rest_framework as df_filters
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.views import BaseTenantViewSet

from .models import AIGeneratedMinuta
from .serializers import AIGeneratedMinutaSerializer
from .ai_service import AIDocumentService


class AIGeneratedMinutaViewSet(BaseTenantViewSet):
    """ViewSet for AI-generated minutas."""
    
    queryset = AIGeneratedMinuta.objects.all().order_by("-created_at")
    serializer_class = AIGeneratedMinutaSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["processo", "status", "gerada_por"]
    search_fields = ["processo__id", "prompt_usuario"]
    ordering_fields = ["created_at", "updated_at", "confidence_score"]

    def perform_create(self, serializer):
        tenant = self._require_tenant()
        serializer.save(tenant=tenant, created_by=self.request.user)


class AIDocumentViewSet(BaseTenantViewSet):
    """ViewSet for AI document operations."""
    
    def get_queryset(self):
        # This viewset doesn't have a specific model, it's for operations
        return None
    
    @action(detail=False, methods=['post'])
    def generate_document(self, request):
        """Generate a document using AI."""
        # Implementation will be added here
        return Response({"message": "AI document generation not yet implemented"})


class GenerateMinutaFromIntentView(APIView):
    """Generate a minuta from user intent using AI."""
    
    def post(self, request):
        """Generate minuta from user intent."""
        # Implementation will be added here
        return Response({"message": "Generate minuta from intent not yet implemented"})


class ApproveMinutaView(APIView):
    """Approve an AI-generated minuta."""
    
    def post(self, request):
        """Approve minuta."""
        # Implementation will be added here
        return Response({"message": "Approve minuta not yet implemented"})


class FinalizeMinutaView(APIView):
    """Finalize an approved minuta."""
    
    def post(self, request):
        """Finalize minuta."""
        # Implementation will be added here
        return Response({"message": "Finalize minuta not yet implemented"})