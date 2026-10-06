"""Update TRELLIS cluster metrics for prioritization."""

from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Q, F
from datetime import datetime, timedelta
from apps.analytics.models import TRELLISInteractionLog, TRELLISClusterMetrics

class Command(BaseCommand):
    help = 'Update TRELLIS cluster metrics for prioritization'
    
    def handle(self, *args, **options):
        # Check if tables exist
        from django.db import connection
        try:
            tables = connection.introspection.table_names()
            if 'trellis_interaction_log' not in tables:
                self.stdout.write(
                    self.style.WARNING('TRELLIS tables do not exist. Run migrations first.')
                )
                return
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error checking tables: {e}')
            )
            return
        
        # Get all unique clusters
        clusters = TRELLISInteractionLog.objects.values_list('matched_cluster', flat=True).distinct()
        
        for cluster_id in clusters:
            if not cluster_id:
                continue
            
            self.stdout.write(f"Updating metrics for {cluster_id}...")
            
            # Get or create metrics record
            metrics, _ = TRELLISClusterMetrics.objects.get_or_create(
                cluster_id=cluster_id,
                defaults={'cluster_name': cluster_id}
            )
            
            # Calculate metrics
            now = datetime.now()
            interactions = TRELLISInteractionLog.objects.filter(matched_cluster=cluster_id)
            
            metrics.total_interactions = interactions.count()
            metrics.interactions_last_7_days = interactions.filter(
                created_at__gte=now - timedelta(days=7)
            ).count()
            metrics.interactions_last_30_days = interactions.filter(
                created_at__gte=now - timedelta(days=30)
            ).count()
            
            # Sentiment metrics
            metrics.negative_sentiment_count = interactions.filter(
                Q(sentiment_score__lt=0) | Q(user_accepted=False)
            ).count()
            metrics.positive_sentiment_count = interactions.filter(
                user_accepted=True
            ).count()
            metrics.avg_sentiment = interactions.aggregate(Avg('sentiment_score'))['sentiment_score__avg'] or 0
            
            # Performance metrics
            metrics.success_rate = interactions.filter(success=True).count() / max(metrics.total_interactions, 1)
            metrics.avg_confidence = interactions.aggregate(Avg('cluster_confidence'))['cluster_confidence__avg'] or 0
            metrics.user_acceptance_rate = interactions.filter(user_accepted=True).count() / max(metrics.total_interactions, 1)
            metrics.user_edit_rate = interactions.filter(user_edited=True).count() / max(metrics.total_interactions, 1)
            metrics.avg_processing_time_ms = interactions.aggregate(Avg('processing_time_ms'))['processing_time_ms__avg'] or 0
            
            # Calculate Oleve priority score
            volume_score = min(metrics.interactions_last_30_days / 100, 10)
            negative_sentiment_score = metrics.negative_sentiment_count / max(metrics.total_interactions, 1) * 10
            achievable_delta = (1 - metrics.success_rate) * 10
            strategic_score = metrics.strategic_priority
            
            metrics.priority_score = volume_score * negative_sentiment_score * achievable_delta * strategic_score
            
            # Flag for refinement if needed
            metrics.needs_refinement = (
                metrics.success_rate < 0.85 or 
                metrics.user_edit_rate > 0.3 or
                metrics.negative_sentiment_count > 10
            )
            
            metrics.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"  ✓ {cluster_id}: {metrics.total_interactions} interactions, "
                    f"priority score: {metrics.priority_score:.2f}"
                )
            )
