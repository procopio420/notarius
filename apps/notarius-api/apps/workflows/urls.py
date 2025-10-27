from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WorkflowTaskViewSet, DocumentoNotaViewSet, NotificationTemplateViewSet, NotificationLogViewSet, FacematchViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'workflow-tasks', WorkflowTaskViewSet, basename='workflow-task')
router.register(r'documento-notas', DocumentoNotaViewSet, basename='documento-nota')
router.register(r'notification-templates', NotificationTemplateViewSet, basename='notification-template')
router.register(r'notification-logs', NotificationLogViewSet, basename='notification-log')
router.register(r'facematch', FacematchViewSet, basename='facematch')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]
