from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AIUsageAnalyticsViewSet
from .trellis_views import TRELLISInteractionViewSet, TRELLISClusterMetricsViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'ai-usage-analytics', AIUsageAnalyticsViewSet, basename='ai-usage-analytics')
router.register(r'trellis-interactions', TRELLISInteractionViewSet, basename='trellis-interaction')
router.register(r'trellis-cluster-metrics', TRELLISClusterMetricsViewSet, basename='trellis-cluster-metrics')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]
