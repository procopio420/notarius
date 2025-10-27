"""
URL configuration for documentos app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DocumentoViewSet, MinutaViewSet, ChecklistViewSet, TemplateViewSet,
    AssinaturaFluxoViewSet, AssinaturaItemViewSet, ClauseLibraryViewSet,
    AIGeneratedMinutaViewSet, AIUsageAnalyticsViewSet, AIDocumentViewSet,
    GenerateMinutaFromIntentView, ApproveMinutaView, FinalizeMinutaView,
    DocumentTemplateViewSet,
)
from .trellis_views import TRELLISInteractionViewSet, TRELLISClusterMetricsViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'documentos', DocumentoViewSet, basename='documento')
router.register(r'minutas', MinutaViewSet, basename='minuta')
router.register(r'checklists', ChecklistViewSet, basename='checklist')
router.register(r'templates', TemplateViewSet, basename='template')
router.register(r'assinatura-fluxos', AssinaturaFluxoViewSet, basename='assinatura-fluxo')
router.register(r'assinatura-itens', AssinaturaItemViewSet, basename='assinatura-item')
router.register(r'clause-library', ClauseLibraryViewSet, basename='clause-library')
router.register(r'ai-generated-minutas', AIGeneratedMinutaViewSet, basename='ai-generated-minuta')
router.register(r'ai-usage-analytics', AIUsageAnalyticsViewSet, basename='ai-usage-analytics')
router.register(r'ai-document', AIDocumentViewSet, basename='ai-document')
router.register(r'document-templates', DocumentTemplateViewSet, basename='document-template')
router.register(r'trellis/interactions', TRELLISInteractionViewSet, basename='trellis-interaction')
router.register(r'trellis/cluster-metrics', TRELLISClusterMetricsViewSet, basename='trellis-metrics')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # AI-specific endpoints
    path('ai/generate-minuta/', GenerateMinutaFromIntentView.as_view(), name='generate-minuta'),
    path('ai/approve-minuta/<uuid:minuta_id>/', ApproveMinutaView.as_view(), name='approve-minuta'),
    path('ai/finalize-minuta/<uuid:minuta_id>/', FinalizeMinutaView.as_view(), name='finalize-minuta'),
]
