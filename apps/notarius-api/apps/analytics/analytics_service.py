"""
Advanced analytics service for Notarius AI system.

This service provides comprehensive analytics and reporting for AI document generation,
including performance metrics, usage patterns, and business intelligence.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.db import models
from django.utils import timezone

from .models import AIUsageAnalytics, AIGeneratedMinuta, ClauseLibrary


class AdvancedAnalyticsService:
    """
    Service for advanced analytics and reporting of AI document generation.
    
    Features:
    - Performance metrics
    - Usage pattern analysis
    - Business intelligence
    - Predictive analytics
    - Export capabilities
    """

    def get_dashboard_data(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive dashboard data for the specified period."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Base queryset for the period
        analytics = AIUsageAnalytics.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Basic metrics
        total_generations = analytics.count()
        approved_generations = analytics.filter(approved=True).count()
        edited_generations = analytics.filter(edited_after_generation=True).count()
        
        # Performance metrics
        avg_confidence = analytics.aggregate(
            avg_conf=models.Avg('confidence_score')
        )['avg_conf'] or 0
        
        avg_generation_time = analytics.aggregate(
            avg_time=models.Avg('generation_time_ms')
        )['avg_time'] or 0
        
        # Document type breakdown
        doc_type_stats = analytics.values('document_type').annotate(
            count=models.Count('id'),
            avg_confidence=models.Avg('confidence_score'),
            avg_time=models.Avg('generation_time_ms'),
            approval_rate=models.Avg('approved')
        ).order_by('-count')
        
        # Daily trends
        daily_trends = self._get_daily_trends(analytics, start_date, end_date)
        
        # Performance distribution
        confidence_distribution = self._get_confidence_distribution(analytics)
        time_distribution = self._get_time_distribution(analytics)
        
        # Top performing clauses
        top_clauses = self._get_top_clauses(tenant_id, days)
        
        # Error analysis
        error_analysis = self._get_error_analysis(analytics)
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "summary": {
                "total_generations": total_generations,
                "approved_generations": approved_generations,
                "edited_generations": edited_generations,
                "approval_rate": (approved_generations / max(total_generations, 1)) * 100,
                "edit_rate": (edited_generations / max(total_generations, 1)) * 100,
                "avg_confidence": round(avg_confidence, 3),
                "avg_generation_time_ms": round(avg_generation_time, 0)
            },
            "document_types": list(doc_type_stats),
            "daily_trends": daily_trends,
            "confidence_distribution": confidence_distribution,
            "time_distribution": time_distribution,
            "top_clauses": top_clauses,
            "error_analysis": error_analysis
        }

    def _get_daily_trends(self, analytics, start_date, end_date) -> List[Dict[str, Any]]:
        """Get daily generation trends."""
        daily_data = analytics.extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            count=models.Count('id'),
            avg_confidence=models.Avg('confidence_score'),
            avg_time=models.Avg('generation_time_ms'),
            approved=models.Sum('approved')
        ).order_by('day')
        
        return [
            {
                "date": item['day'],
                "generations": item['count'],
                "avg_confidence": round(item['avg_confidence'] or 0, 3),
                "avg_time_ms": round(item['avg_time'] or 0, 0),
                "approved": item['approved']
            }
            for item in daily_data
        ]

    def _get_confidence_distribution(self, analytics) -> Dict[str, int]:
        """Get distribution of confidence scores."""
        ranges = [
            (0.0, 0.5, "low"),
            (0.5, 0.7, "medium"),
            (0.7, 0.9, "high"),
            (0.9, 1.0, "very_high")
        ]
        
        distribution = {}
        for min_conf, max_conf, label in ranges:
            count = analytics.filter(
                confidence_score__gte=min_conf,
                confidence_score__lt=max_conf
            ).count()
            distribution[label] = count
        
        return distribution

    def _get_time_distribution(self, analytics) -> Dict[str, int]:
        """Get distribution of generation times."""
        ranges = [
            (0, 1000, "fast"),
            (1000, 3000, "medium"),
            (3000, 5000, "slow"),
            (5000, float('inf'), "very_slow")
        ]
        
        distribution = {}
        for min_time, max_time, label in ranges:
            if max_time == float('inf'):
                count = analytics.filter(generation_time_ms__gte=min_time).count()
            else:
                count = analytics.filter(
                    generation_time_ms__gte=min_time,
                    generation_time_ms__lt=max_time
                ).count()
            distribution[label] = count
        
        return distribution

    def _get_top_clauses(self, tenant_id: str, days: int) -> List[Dict[str, Any]]:
        """Get top performing clauses."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get clauses with usage in AI generations
        ai_generations = AIGeneratedMinuta.objects.filter(
            tenant_id=tenant_id,
            generation_timestamp__gte=start_date
        )
        
        # Count clause usage
        clause_usage = {}
        for generation in ai_generations:
            for clause_id in generation.clauses_used:
                clause_usage[clause_id] = clause_usage.get(clause_id, 0) + 1
        
        # Get clause details
        top_clauses = []
        for clause_id, usage_count in sorted(clause_usage.items(), key=lambda x: x[1], reverse=True)[:10]:
            try:
                clause = ClauseLibrary.objects.get(id=clause_id, tenant_id=tenant_id)
                top_clauses.append({
                    "clause_id": clause_id,
                    "nome": clause.nome,
                    "categoria": clause.categoria,
                    "usage_count": usage_count,
                    "total_usage": clause.frequencia_uso
                })
            except ClauseLibrary.DoesNotExist:
                continue
        
        return top_clauses

    def _get_error_analysis(self, analytics) -> Dict[str, Any]:
        """Analyze errors and low-confidence generations."""
        low_confidence = analytics.filter(confidence_score__lt=0.7)
        slow_generations = analytics.filter(generation_time_ms__gt=5000)
        rejected_generations = analytics.filter(approved=False)
        
        return {
            "low_confidence_count": low_confidence.count(),
            "slow_generations_count": slow_generations.count(),
            "rejected_count": rejected_generations.count(),
            "low_confidence_rate": (low_confidence.count() / max(analytics.count(), 1)) * 100,
            "slow_generation_rate": (slow_generations.count() / max(analytics.count(), 1)) * 100,
            "rejection_rate": (rejected_generations.count() / max(analytics.count(), 1)) * 100
        }

    def get_performance_report(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get detailed performance report."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = AIUsageAnalytics.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Performance metrics by document type
        doc_type_performance = analytics.values('document_type').annotate(
            count=models.Count('id'),
            avg_confidence=models.Avg('confidence_score'),
            avg_time=models.Avg('generation_time_ms'),
            approval_rate=models.Avg('approved'),
            edit_rate=models.Avg('edited_after_generation'),
            min_confidence=models.Min('confidence_score'),
            max_confidence=models.Max('confidence_score'),
            min_time=models.Min('generation_time_ms'),
            max_time=models.Max('generation_time_ms')
        ).order_by('-count')
        
        # Hourly patterns (SQLite compatible)
        hourly_patterns = analytics.extra(
            select={'hour': 'strftime(\'%H\', created_at)'}
        ).values('hour').annotate(
            count=models.Count('id'),
            avg_confidence=models.Avg('confidence_score')
        ).order_by('hour')
        
        # Model performance comparison
        model_performance = analytics.values('ai_model_version').annotate(
            count=models.Count('id'),
            avg_confidence=models.Avg('confidence_score'),
            avg_time=models.Avg('generation_time_ms'),
            approval_rate=models.Avg('approved')
        ).order_by('-count')
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "document_type_performance": list(doc_type_performance),
            "hourly_patterns": list(hourly_patterns),
            "model_performance": list(model_performance)
        }

    def get_usage_insights(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get usage insights and recommendations."""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        analytics = AIUsageAnalytics.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # Usage patterns
        total_generations = analytics.count()
        unique_days = analytics.extra(
            select={'day': 'date(created_at)'}
        ).values('day').distinct().count()
        
        avg_daily_usage = total_generations / max(unique_days, 1)
        
        # Peak usage times (SQLite compatible)
        peak_hours = analytics.extra(
            select={'hour': 'strftime(\'%H\', created_at)'}
        ).values('hour').annotate(
            count=models.Count('id')
        ).order_by('-count')[:3]
        
        # Most common document types
        popular_docs = analytics.values('document_type').annotate(
            count=models.Count('id')
        ).order_by('-count')[:5]
        
        # Recommendations
        recommendations = self._generate_recommendations(analytics)
        
        return {
            "usage_patterns": {
                "total_generations": total_generations,
                "unique_days": unique_days,
                "avg_daily_usage": round(avg_daily_usage, 1),
                "peak_hours": list(peak_hours)
            },
            "popular_documents": list(popular_docs),
            "recommendations": recommendations
        }

    def _generate_recommendations(self, analytics) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on analytics."""
        recommendations = []
        
        # Low confidence recommendation
        low_conf_count = analytics.filter(confidence_score__lt=0.7).count()
        if low_conf_count > 0:
            recommendations.append({
                "type": "warning",
                "title": "Low Confidence Generations",
                "message": f"{low_conf_count} generations had confidence below 70%. Consider improving command clarity.",
                "action": "Review and improve command templates"
            })
        
        # Slow generation recommendation
        slow_count = analytics.filter(generation_time_ms__gt=5000).count()
        if slow_count > 0:
            recommendations.append({
                "type": "performance",
                "title": "Slow Generation Times",
                "message": f"{slow_count} generations took longer than 5 seconds. Consider optimizing templates.",
                "action": "Optimize template complexity"
            })
        
        # High edit rate recommendation
        total = analytics.count()
        edited = analytics.filter(edited_after_generation=True).count()
        if total > 0 and (edited / total) > 0.3:
            recommendations.append({
                "type": "quality",
                "title": "High Edit Rate",
                "message": f"{(edited/total)*100:.1f}% of generated documents were edited. Consider improving templates.",
                "action": "Review and update document templates"
            })
        
        return recommendations

    def export_analytics(self, tenant_id: str, days: int = 30, format: str = 'json') -> Dict[str, Any]:
        """Export analytics data in various formats."""
        dashboard_data = self.get_dashboard_data(tenant_id, days)
        performance_report = self.get_performance_report(tenant_id, days)
        usage_insights = self.get_usage_insights(tenant_id, days)
        
        export_data = {
            "export_info": {
                "tenant_id": tenant_id,
                "exported_at": timezone.now().isoformat(),
                "period_days": days,
                "format": format
            },
            "dashboard": dashboard_data,
            "performance": performance_report,
            "insights": usage_insights
        }
        
        return export_data
