"""
Workflow and notification views for Notarius.

This module contains viewsets for workflow tasks, notifications,
internal notes, and facematch identity verification.
"""

from django.contrib.auth.models import User
from django_filters import rest_framework as df_filters
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.base.views import BaseTenantViewSet

from .models import WorkflowTask, DocumentoNota, NotificationTemplate, NotificationLog
from .serializers import (
    DocumentoNotaSerializer, NotificationLogSerializer, 
    NotificationTemplateSerializer, WorkflowTaskSerializer
)
from .facematch_service import FacematchService
from .notification_service import NotificationService
from .workflow_service import WorkflowService
from apps.documentos.models import Documento


class DocumentoNotaViewSet(BaseTenantViewSet):
    queryset = DocumentoNota.objects.all().order_by("-created_at")
    serializer_class = DocumentoNotaSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["documento", "is_private", "is_resolved", "created_by"]
    search_fields = ["titulo", "conteudo"]
    ordering_fields = ["created_at", "titulo"]

    def perform_create(self, serializer):
        tenant = self._require_tenant()
        serializer.save(tenant=tenant, created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Mark a note as resolved."""
        nota = self.get_object()
        nota.is_resolved = True
        nota.save()
        
        serializer = self.get_serializer(nota)
        return Response(serializer.data)


class WorkflowTaskViewSet(BaseTenantViewSet):
    queryset = WorkflowTask.objects.all().order_by("-created_at")
    serializer_class = WorkflowTaskSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tipo", "prioridade", "status", "assigned_to", "created_by"]
    search_fields = ["titulo", "descricao"]
    ordering_fields = ["created_at", "deadline", "prioridade"]

    def perform_create(self, serializer):
        tenant = self._require_tenant()
        serializer.save(tenant=tenant, created_by=self.request.user)

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        """Get task dashboard data."""
        tenant = self._require_tenant()
        user = request.user if request.query_params.get("user_specific") else None
        
        try:
            workflow_service = WorkflowService()
            dashboard_data = workflow_service.get_task_dashboard(str(tenant.id), user)
            return Response(dashboard_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["get"])
    def authentication_queue(self, request):
        """Get pending authentication tasks."""
        tenant = self._require_tenant()
        
        try:
            workflow_service = WorkflowService()
            queue_data = workflow_service.get_authentication_queue(str(tenant.id))
            return Response({"authentication_queue": queue_data})
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["get"])
    def signature_queue(self, request):
        """Get pending signature tasks."""
        tenant = self._require_tenant()
        
        try:
            workflow_service = WorkflowService()
            queue_data = workflow_service.get_signature_queue(str(tenant.id))
            return Response({"signature_queue": queue_data})
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["get"])
    def review_queue(self, request):
        """Get pending review tasks."""
        tenant = self._require_tenant()
        
        try:
            workflow_service = WorkflowService()
            queue_data = workflow_service.get_review_queue(str(tenant.id))
            return Response({"review_queue": queue_data})
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Assign a task to a user."""
        task = self.get_object()
        assigned_to_id = request.data.get("assigned_to")
        
        if not assigned_to_id:
            return Response(
                {"error": "assigned_to is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assigned_to = User.objects.get(id=assigned_to_id)
            
            workflow_service = WorkflowService()
            updated_task = workflow_service.assign_task(
                str(task.id), assigned_to, request.user
            )
            
            serializer = self.get_serializer(updated_task)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark a task as completed."""
        task = self.get_object()
        notes = request.data.get("notes", "")
        
        try:
            workflow_service = WorkflowService()
            completed_task = workflow_service.complete_task(
                str(task.id), request.user, notes
            )
            
            serializer = self.get_serializer(completed_task)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class NotificationTemplateViewSet(BaseTenantViewSet):
    queryset = NotificationTemplate.objects.all().order_by("nome")
    serializer_class = NotificationTemplateSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["tipo", "trigger", "is_active"]
    search_fields = ["nome", "assunto", "corpo"]
    ordering_fields = ["nome", "created_at"]

    def perform_create(self, serializer):
        tenant = self._require_tenant()
        serializer.save(tenant=tenant, created_by=self.request.user)


class NotificationLogViewSet(BaseTenantViewSet):
    queryset = NotificationLog.objects.all().order_by("-created_at")
    serializer_class = NotificationLogSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["template", "status", "recipient_email"]
    search_fields = ["recipient_name", "recipient_email", "rendered_subject"]
    ordering_fields = ["created_at", "sent_at"]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get notification statistics."""
        tenant = self._require_tenant()
        days = int(request.query_params.get("days", 30))
        
        try:
            notification_service = NotificationService()
            stats_data = notification_service.get_notification_stats(str(tenant.id), days)
            return Response(stats_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class FacematchViewSet(BaseTenantViewSet):
    """Facematch identity verification endpoints."""
    
    @action(detail=False, methods=["post"])
    def verify_identity(self, request):
        """Verify identity using face matching."""
        documento_id = request.data.get("documento_id")
        selfie_image = request.data.get("selfie_image")
        
        if not documento_id or not selfie_image:
            return Response(
                {"error": "documento_id and selfie_image are required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tenant = self._require_tenant()
            documento = Documento.objects.get(id=documento_id, tenant=tenant)
            
            facematch_service = FacematchService()
            result = facematch_service.verify_identity(
                documento=documento,
                selfie_image=selfie_image,
                user_id=str(request.user.id),
                tenant_id=str(tenant.id)
            )
            
            return Response(result)
        except Documento.DoesNotExist:
            return Response(
                {"error": "Document not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["post"])
    def validate_image(self, request):
        """Validate image quality for face matching."""
        image_data = request.data.get("image_data")
        
        if not image_data:
            return Response(
                {"error": "image_data is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            facematch_service = FacematchService()
            result = facematch_service.validate_image_quality(image_data)
            return Response(result)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get facematch verification statistics."""
        tenant = self._require_tenant()
        days = int(request.query_params.get("days", 30))
        
        try:
            facematch_service = FacematchService()
            stats_data = facematch_service.get_verification_stats(str(tenant.id), days)
            return Response(stats_data)
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
