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
from .models import DocumentTemplate, Template
from .serializers import DocumentTemplateSerializer, TemplateSerializer
from .template_service import TemplateService
from .pdf_service import PDFService


class TemplateViewSet(BaseTenantViewSet):
    queryset = Template.objects.all().order_by("-created_at")
    serializer_class = TemplateSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["document_type", "is_active", "version", "source"]
    search_fields = ["name", "document_type"]
    ordering_fields = ["name", "created_at", "version"]

    def perform_create(self, serializer):
        tenant = self._require_tenant()
        serializer.save(tenant=tenant, created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def preview(self, request, pk=None):
        """Preview template with provided variables."""
        template = self.get_object()
        variaveis = request.data.get("variaveis", {})
        
        try:
            template_service = TemplateService()
            rendered_content = template_service.render_template(str(template.id), variaveis)
            return Response({"rendered_content": rendered_content})
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"])
    def render_pdf(self, request, pk=None):
        """Generate PDF from template with variables."""
        template = self.get_object()
        variaveis = request.data.get("variaveis", {})
        
        try:
            pdf_service = PDFService()
            pdf_bytes, filename = pdf_service.generate_pdf_from_template(
                str(template.id), variaveis
            )
            
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
        except Exception as e:
            return Response(
                {"error": str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class DocumentTemplateViewSet(BaseTenantViewSet):
    """ViewSet for managing document templates."""
    
    queryset = DocumentTemplate.objects.all().order_by("-created_at")
    serializer_class = DocumentTemplateSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["document_type", "is_default", "is_active", "version"]
    search_fields = ["name", "description", "document_type"]
    ordering_fields = ["name", "created_at", "updated_at", "version"]
    
    def perform_create(self, serializer):
        """Create template with proper defaults."""
        tenant = self._require_tenant()
        serializer.save(
            tenant=tenant,
            created_by=self.request.user,
            is_default=False,  # User-created templates are not default
        )
    
    def perform_update(self, serializer):
        """Update template with audit info."""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=["post"])
    def preview(self, request, pk=None):
        """Preview template with sample data."""
        template = self.get_object()
        
        try:
            # Get sample minuta for preview
            from apps.documentos.models import Minuta
            sample_minuta = Minuta.objects.filter(
                tenant=template.tenant,
                status="aprovado"
            ).first()
            
            if not sample_minuta:
                return Response(
                    {"error": "No sample minuta available for preview"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Use document finalizer to generate preview
            from apps.documentos.finalizer import get_document_finalizer
            
            finalizer = get_document_finalizer()
            
            # Generate preview HTML
            html_content = finalizer._markdown_to_html(sample_minuta.corpo_md)
            
            context = {
                'content': html_content,
                'minuta': sample_minuta,
                'tenant_id': template.tenant.id,
                'generated_at': datetime.now(),
                'citations': sample_minuta.citations,
                'grounding_confidence': sample_minuta.grounding_confidence,
                'template': template,
            }
            
            # Render template
            from django.template.loader import render_to_string
            template_path = template.get_template_path()
            html_template = render_to_string(template_path, context)
            
            return Response({
                "preview_html": html_template,
                "template_info": {
                    "name": template.name,
                    "document_type": template.document_type,
                    "version": template.version,
                }
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to generate preview: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=["post"])
    def test_pdf(self, request, pk=None):
        """Test PDF generation with template."""
        template = self.get_object()
        
        try:
            # Get sample minuta for testing
            from apps.documentos.models import Minuta
            sample_minuta = Minuta.objects.filter(
                tenant=template.tenant,
                status="aprovado"
            ).first()
            
            if not sample_minuta:
                return Response(
                    {"error": "No sample minuta available for testing"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Use document finalizer to generate test PDF
            from apps.documentos.finalizer import get_document_finalizer
            
            finalizer = get_document_finalizer()
            
            # Generate test PDF
            pdf_bytes, filename = asyncio.run(
                finalizer._generate_pdf(
                    content=sample_minuta.corpo_md,
                    minuta=sample_minuta,
                    tenant_id=template.tenant.id
                )
            )
            
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="test_{filename}"'
            return response
            
        except Exception as e:
            return Response(
                {"error": f"Failed to generate test PDF: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=["get"])
    def by_type(self, request):
        """Get templates by document type."""
        document_type = request.query_params.get("document_type")
        
        if not document_type:
            return Response(
                {"error": "document_type parameter is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            tenant = self._require_tenant()
            
            # Get tenant-specific template, fallback to default
            template = DocumentTemplate.get_tenant_template(
                tenant=tenant,
                document_type=document_type
            )
            
            if not template:
                return Response(
                    {"error": f"No template found for document type: {document_type}"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(template)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to get template: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=["get"])
    def available_types(self, request):
        """Get available document types with template counts."""
        try:
            tenant = self._require_tenant()
            
            # Get all document types with template counts
            types_with_counts = DocumentTemplate.objects.filter(
                tenant=tenant,
                is_active=True
            ).values('document_type').annotate(
                count=models.Count('id'),
                has_default=models.Case(
                    models.When(is_default=True, then=True),
                    default=False,
                    output_field=models.BooleanField()
                )
            ).order_by('document_type')
            
            return Response({
                "document_types": list(types_with_counts),
                "total_templates": sum(item['count'] for item in types_with_counts)
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to get document types: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
