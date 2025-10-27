from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TemplateViewSet, DocumentTemplateViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'templates', TemplateViewSet, basename='template')
router.register(r'document-templates', DocumentTemplateViewSet, basename='document-template')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]
