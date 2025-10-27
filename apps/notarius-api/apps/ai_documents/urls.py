from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIGeneratedMinutaViewSet, AIDocumentViewSet, GenerateMinutaFromIntentView, ApproveMinutaView, FinalizeMinutaView

# Create router and register viewsets
router = DefaultRouter()
router.register(r'ai-generated-minutas', AIGeneratedMinutaViewSet, basename='ai-generated-minuta')
router.register(r'ai-documents', AIDocumentViewSet, basename='ai-document')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # AI document generation endpoints
    path('generate-minuta-from-intent/', GenerateMinutaFromIntentView.as_view(), name='generate-minuta-from-intent'),
    path('approve-minuta/', ApproveMinutaView.as_view(), name='approve-minuta'),
    path('finalize-minuta/', FinalizeMinutaView.as_view(), name='finalize-minuta'),
]
