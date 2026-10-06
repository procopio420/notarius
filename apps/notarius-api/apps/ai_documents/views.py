"""
AI Documents views for Notarius.

This module contains viewsets for AI-generated documents and related functionality.
"""

import asyncio
import logging
import time
import traceback
from uuid import UUID

from django.contrib.auth.models import User
from django.conf import settings
from django_filters import rest_framework as df_filters
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.views import BaseTenantViewSet, get_tenant_for_request
from apps.documentos.models import Minuta
from apps.ai.clients import get_ai_service_manager

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
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Generate minuta from user intent."""
        # Get tenant and user (fallback to user's default_tenant if no X-Tenant-ID)
        tenant = get_tenant_for_request(request)
        if tenant is None:
            raise PermissionDenied("Tenant não definido. Envie X-Tenant-ID.")
        
        user = request.user
        if not user or not user.is_authenticated:
            raise PermissionDenied("Usuário não autenticado.")
        
        # Get request data
        intent = request.data.get('intent') or request.data.get('command')
        processo_id = request.data.get('processo_id')
        
        if not intent:
            raise ValidationError({"intent": "Campo 'intent' ou 'command' é obrigatório."})
        
        if not processo_id:
            raise ValidationError({"processo_id": "Campo 'processo_id' é obrigatório."})
        
        try:
            processo_uuid = UUID(processo_id)
        except (ValueError, TypeError):
            raise ValidationError({"processo_id": "processo_id deve ser um UUID válido."})
        
        start_time = time.time()
        
        try:
            # Get AI service manager
            ai_service = get_ai_service_manager()
            
            # Get user UUID from profile if available, otherwise None
            # Django User model uses integer IDs, but UserProfile has UUID
            user_uuid = None
            if hasattr(user, 'profile') and user.profile:
                user_uuid = user.profile.id
            # If no profile, user_id will be None (optional parameter)
            
            # Generate minuta from intent (async call)
            minuta_data = asyncio.run(
                ai_service.generate_minuta_from_intent(
                    command=intent,
                    tenant_id=UUID(str(tenant.id)),
                    user_id=user_uuid,
                    processo_id=processo_uuid
                )
            )
            
            # Get the processo to verify it exists and belongs to tenant
            from apps.processos.models import Processo
            try:
                processo = Processo.objects.get(id=processo_uuid, tenant=tenant)
            except Processo.DoesNotExist:
                raise ValidationError({"processo_id": "Processo não encontrado ou não pertence ao tenant."})
            
            # Get last version to determine next version
            last_minuta = Minuta.objects.filter(processo=processo).order_by('-versao').first()
            next_version = (last_minuta.versao + 1) if last_minuta else 1
            
            # Create Minuta
            minuta = Minuta.objects.create(
                tenant=tenant,
                processo=processo,
                versao=next_version,
                gerada_por='ia',
                status='rascunho',
                corpo_md=minuta_data.get('corpo_md', ''),
                variaveis_json=minuta_data.get('variaveis_json', {}),
                citations=minuta_data.get('citations', []),
                grounding_confidence=minuta_data.get('grounding_confidence', 0.0),
                skeleton_cache_key=minuta_data.get('skeleton_cache_key', ''),
                created_by=user,
            )
            
            # Create AI generation tracking record
            generation_time_ms = int((time.time() - start_time) * 1000)
            
            ai_generation = AIGeneratedMinuta.objects.create(
                tenant=tenant,
                minuta=minuta,
                original_command=intent,
                parsed_intent=minuta_data.get('parsed_intent', {}),
                ai_model_version='intent-engine',
                confidence_score=minuta_data.get('grounding_confidence', 0.0),
                generation_time_ms=generation_time_ms,
                clauses_used=[],
                template_source='ai_generated',
            )
            
            # Return minuta data
            from apps.documentos.serializers import MinutaSerializer
            serializer = MinutaSerializer(minuta)
            response_data = serializer.data
            response_data['grounding_confidence'] = minuta_data.get('grounding_confidence', 0.0)
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except ValidationError:
            raise
        except PermissionDenied:
            raise
        except Exception as e:
            logger = logging.getLogger(__name__)
            error_details = {
                "error": str(e),
                "error_type": type(e).__name__,
            }
            logger.error(
                f"Failed to generate minuta from intent: {e}",
                exc_info=True,
                extra={
                    "intent": intent[:100] if intent else None,
                    "processo_id": str(processo_id) if processo_id else None,
                    "tenant_id": str(tenant.id) if tenant else None,
                    "user_id": str(user.id) if user else None,
                }
            )
            # In debug mode, include more details
            if getattr(settings, 'DEBUG', False):
                error_details["traceback"] = traceback.format_exc()
            
            return Response(
                error_details,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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