"""TRELLIS-specific API endpoints."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.base.views import BaseTenantViewSet
from .models import TRELLISInteractionLog, TRELLISClusterMetrics
from .serializers import TRELLISInteractionLogSerializer, TRELLISClusterMetricsSerializer

class TRELLISInteractionViewSet(BaseTenantViewSet):
    """ViewSet for TRELLIS interaction logging and feedback."""
    queryset = TRELLISInteractionLog.objects.all()
    serializer_class = TRELLISInteractionLogSerializer
    
    def create(self, request):
        """Log a TRELLIS interaction."""
        tenant = self._require_tenant()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(tenant=tenant)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['patch'])
    def feedback(self, request, pk=None):
        """Update interaction with user feedback."""
        interaction = self.get_object()
        
        # Update feedback fields
        interaction.user_accepted = request.data.get('user_accepted')
        interaction.user_edited = request.data.get('user_edited', False)
        interaction.sentiment_score = request.data.get('sentiment_score')
        interaction.user_feedback_text = request.data.get('user_feedback_text', '')
        interaction.save()
        
        return Response({'message': 'Feedback recorded'})

class TRELLISClusterMetricsViewSet(BaseTenantViewSet):
    """ViewSet for TRELLIS cluster metrics and prioritization."""
    queryset = TRELLISClusterMetrics.objects.all()
    serializer_class = TRELLISClusterMetricsSerializer
    
    @action(detail=False, methods=['post'])
    def compute_priority_scores(self, request):
        """Compute priority scores using Oleve formula."""
        tenant = self._require_tenant()
        
        # Recompute scores for all clusters
        clusters = TRELLISClusterMetrics.objects.filter(tenant=tenant)
        
        for cluster in clusters:
            # Oleve formula: volume x negative_sentiment x achievable_delta x strategic_relevance
            volume_score = min(cluster.interactions_last_30_days / 100, 10)  # Normalize to 0-10
            negative_sentiment_score = cluster.negative_sentiment_count / max(cluster.total_interactions, 1) * 10
            achievable_delta = (1 - cluster.success_rate) * 10  # Higher potential improvement = higher score
            strategic_score = cluster.strategic_priority  # 1-10 scale
            
            cluster.priority_score = volume_score * negative_sentiment_score * achievable_delta * strategic_score
            cluster.save()
        
        return Response({'message': f'Recomputed {clusters.count()} cluster scores'})
    
    @action(detail=False, methods=['get'])
    def top_priorities(self, request):
        """Get top priority clusters for refinement."""
        tenant = self._require_tenant()
        top_n = int(request.query_params.get('top_n', 10))
        
        top_clusters = TRELLISClusterMetrics.objects.filter(
            tenant=tenant,
            is_active=True
        ).order_by('-priority_score')[:top_n]
        
        serializer = self.get_serializer(top_clusters, many=True)
        return Response({'top_priorities': serializer.data})
