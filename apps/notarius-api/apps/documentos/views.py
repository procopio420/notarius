import asyncio
from datetime import datetime
from django.conf import settings
from django.db import models
from django.http import HttpResponse
from django_filters import rest_framework as df_filters
from rest_framework import filters, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.views import BaseTenantViewSet

from .models import (
    Documento, Minuta
)
from .serializers import (
    DocumentoSerializer, MinutaSerializer
)
# Import services that are actually used
from .storage_service import StorageService


class DocumentoFilter(df_filters.FilterSet):
    status = df_filters.CharFilter(field_name="status", lookup_expr="iexact")
    processo = df_filters.UUIDFilter(field_name="processo__id")

    class Meta:
        model = Documento
        fields = ["status", "processo"]


class DocumentoViewSet(BaseTenantViewSet):
    queryset = Documento.objects.all().order_by("-created_at")
    serializer_class = DocumentoSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DocumentoFilter
    search_fields = ["s3_key", "processo__id"]
    ordering_fields = ["created_at", "updated_at", "status", "pages"]
    parser_classes = [MultiPartParser, FormParser]
    
    # Service instances to avoid repeated instantiation
    _storage_service = None
    
    @property
    def storage_service(self):
        if self._storage_service is None:
            self._storage_service = StorageService()
        return self._storage_service
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload a new document file."""
        tenant = self._require_tenant()
        
        if 'file' not in request.FILES:
            return Response(
                {"error": "No file provided"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_obj = request.FILES['file']
        processo_id = request.data.get('processo_id')
        
        if not processo_id:
            return Response(
                {"error": "processo_id is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Upload to S3
            s3_key, file_hash = self.storage_service.upload_file(
                file_obj=file_obj,
                tenant_id=str(tenant.id),
                processo_id=processo_id,
                filename=file_obj.name,
                content_type=file_obj.content_type
            )
            
            # Create Documento record
            documento = Documento.objects.create(
                tenant=tenant,
                processo_id=processo_id,
                s3_key=s3_key,
                hash_sha256=file_hash,
                mime=file_obj.content_type,
                status="novo"
            )
            
            # Create audit log
            from apps.auditoria.models import AuditLog
            AuditLog.objects.create(
                tenant=tenant,
                actor=request.user,
                resource_type="documento",
                resource_id=documento.id,
                action="create",
                diff_json={
                    "filename": file_obj.name,
                    "file_size": file_obj.size,
                    "content_type": file_obj.content_type,
                },
                extra={
                    "processo_id": processo_id,
                    "s3_key": s3_key,
                }
            )
            
            serializer = self.get_serializer(documento)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Upload failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download document file."""
        documento = self.get_object()
        # Safeguard: reload to ensure we have the latest data
        documento.reload()
        
        try:
            file_content = documento.get_file_content()
            response = HttpResponse(file_content, content_type=documento.mime)
            response['Content-Disposition'] = f'attachment; filename="{documento.s3_key.split("/")[-1]}"'
            return response
        except Exception as e:
            return Response(
                {"error": f"Download failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def presigned_url(self, request, pk=None):
        """Get presigned URL for document download."""
        documento = self.get_object()
        expiry_hours = int(request.query_params.get('expiry_hours', 1))
        
        try:
            url = documento.get_presigned_url(expiry_hours)
            return Response({"url": url, "expires_in_hours": expiry_hours})
        except Exception as e:
            return Response(
                {"error": f"Failed to generate presigned URL: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MinutaViewSet(BaseTenantViewSet):
    queryset = Minuta.objects.all().order_by("-created_at")
    serializer_class = MinutaSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["processo", "gerada_por", "versao"]
    search_fields = ["processo__id"]
    ordering_fields = ["created_at", "versao"]

    def perform_create(self, serializer):
        tenant = self._require_tenant()
        serializer.save(tenant=tenant, created_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='rewrite_with_ai')
    def rewrite_with_ai(self, request, pk=None):
        """Rewrite minuta content using AI based on user prompt."""
        minuta = self.get_object()
        
        # Only allow AI rewriting for draft minutas
        if minuta.status != 'rascunho':
            return Response(
                {"error": "Apenas minutas em rascunho podem ser reescritas"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        improvement_prompt = request.data.get('improvement_prompt')
        selected_text = request.data.get('selected_text')
        
        if not improvement_prompt:
            return Response(
                {"error": "Prompt de melhoria é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Determine if this is a partial rewrite
            is_partial = bool(selected_text)
            content_to_rewrite = selected_text if is_partial else minuta.corpo_md
            
            # Use AIDocumentService for rewriting
            from apps.ai_documents.ai_service import AIDocumentService
            ai_service = AIDocumentService()
            
            # Use asyncio.run to call async method
            rewritten_content = asyncio.run(ai_service.rewrite_document_content(
                content=content_to_rewrite,
                improvement_prompt=improvement_prompt,
                is_partial=is_partial
            ))
            
            # Track AI usage
            from apps.auditoria.models import AuditLog
            AuditLog.objects.create(
                tenant=request.tenant,
                actor=request.user,
                resource_type='minuta',
                resource_id=minuta.id,
                action='ai_rewrite',
                details={
                    'improvement_prompt': improvement_prompt,
                    'is_partial': is_partial,
                    'content_length_before': len(content_to_rewrite),
                    'content_length_after': len(rewritten_content),
                    'method': 'intent-engine-microservice'
                }
            )
            
            # Update minuta content
            if is_partial:
                # Replace only the selected text
                minuta.corpo_md = minuta.corpo_md.replace(selected_text, rewritten_content)
            else:
                minuta.corpo_md = rewritten_content
            minuta.save()
            
            serializer = self.get_serializer(minuta)
            return Response(serializer.data)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error rewriting minuta content with AI: {e}", exc_info=True)
            return Response(
                {"error": f"Falha ao reescrever conteúdo com IA: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )