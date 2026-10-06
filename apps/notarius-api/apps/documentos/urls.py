"""
URL configuration for documentos app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    DocumentoViewSet, MinutaViewSet,
)
# Import AI views from ai_documents app (for function-based views)
from apps.ai_documents.views import (
    GenerateMinutaFromIntentView, ApproveMinutaView, FinalizeMinutaView,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'documentos', DocumentoViewSet, basename='documento')
router.register(r'minutas', MinutaViewSet, basename='minuta')
# Note: Other viewsets are registered in their respective apps:
# - templates: apps/templates/urls.py
# - analytics: apps/analytics/urls.py
# - ai-generated-minutas, ai-document: apps/ai_documents/urls.py

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # AI-specific endpoints
    path('ai/generate-minuta/', GenerateMinutaFromIntentView.as_view(), name='generate-minuta'),
    path('ai/approve-minuta/<uuid:minuta_id>/', ApproveMinutaView.as_view(), name='approve-minuta'),
    path('ai/finalize-minuta/<uuid:minuta_id>/', FinalizeMinutaView.as_view(), name='finalize-minuta'),
]
