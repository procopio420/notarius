"""
Prometheus metrics collection for all services
"""

import time
import logging
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client.exposition import CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Prometheus metrics collector for services."""
    
    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.registry = CollectorRegistry()
        self._setup_metrics()
    
    def _setup_metrics(self):
        """Initialize Prometheus metrics."""
        try:
            # Service info
            self.service_info = Info(
                'service_info',
                'Service information',
                registry=self.registry
            )
            self.service_info.info({
                'name': self.service_name,
                'version': self.service_version,
            })
            
            # Request metrics
            self.request_count = Counter(
                'http_requests_total',
                'Total HTTP requests',
                ['method', 'endpoint', 'status_code', 'service'],
                registry=self.registry
            )
            
            self.request_duration = Histogram(
                'http_request_duration_seconds',
                'HTTP request duration in seconds',
                ['method', 'endpoint', 'service'],
                registry=self.registry
            )
            
            # PII Vault metrics
            self.pii_tokenize_count = Counter(
                'pii_tokenize_total',
                'Total PII tokenization operations',
                ['scope', 'service'],
                registry=self.registry
            )
            
            self.pii_tokenize_duration = Histogram(
                'pii_tokenize_duration_seconds',
                'PII tokenization duration in seconds',
                ['scope', 'service'],
                registry=self.registry
            )
            
            self.pii_detokenize_count = Counter(
                'pii_detokenize_total',
                'Total PII detokenization operations',
                ['scope', 'service'],
                registry=self.registry
            )
            
            self.pii_detokenize_duration = Histogram(
                'pii_detokenize_duration_seconds',
                'PII detokenization duration in seconds',
                ['scope', 'service'],
                registry=self.registry
            )
            
            # LexNode metrics
            self.lexnode_retrieve_count = Counter(
                'lexnode_retrieve_total',
                'Total LexNode retrieval operations',
                ['service'],
                registry=self.registry
            )
            
            self.lexnode_retrieve_duration = Histogram(
                'lexnode_retrieve_duration_seconds',
                'LexNode retrieval duration in seconds',
                ['service'],
                registry=self.registry
            )
            
            self.lexnode_cache_hits = Counter(
                'lexnode_cache_hits_total',
                'Total LexNode cache hits',
                ['service'],
                registry=self.registry
            )
            
            self.lexnode_cache_misses = Counter(
                'lexnode_cache_misses_total',
                'Total LexNode cache misses',
                ['service'],
                registry=self.registry
            )
            
            # Intent Engine metrics
            self.intent_parse_count = Counter(
                'intent_parse_total',
                'Total intent parsing operations',
                ['service'],
                registry=self.registry
            )
            
            self.intent_parse_duration = Histogram(
                'intent_parse_duration_seconds',
                'Intent parsing duration in seconds',
                ['service'],
                registry=self.registry
            )
            
            self.intent_confidence = Histogram(
                'intent_confidence_score',
                'Intent confidence score distribution',
                ['service'],
                registry=self.registry
            )
            
            # AI metrics
            self.ai_draft_generation_count = Counter(
                'ai_draft_generation_total',
                'Total AI draft generation operations',
                ['service'],
                registry=self.registry
            )
            
            self.ai_draft_generation_duration = Histogram(
                'ai_draft_generation_duration_seconds',
                'AI draft generation duration in seconds',
                ['service'],
                registry=self.registry
            )
            
            self.ai_draft_edit_rate = Histogram(
                'ai_draft_edit_rate',
                'AI draft edit rate (how much was changed)',
                ['service'],
                registry=self.registry
            )
            
            # Document metrics
            self.document_finalization_count = Counter(
                'document_finalization_total',
                'Total document finalization operations',
                ['service'],
                registry=self.registry
            )
            
            self.document_finalization_duration = Histogram(
                'document_finalization_duration_seconds',
                'Document finalization duration in seconds',
                ['service'],
                registry=self.registry
            )
            
            # Error metrics
            self.error_count = Counter(
                'errors_total',
                'Total errors',
                ['error_type', 'service'],
                registry=self.registry
            )
            
            # PII leak detection
            self.pii_leak_alerts = Counter(
                'pii_leak_alerts_total',
                'Total PII leak alerts',
                ['service'],
                registry=self.registry
            )
            
            # System metrics
            self.active_connections = Gauge(
                'active_connections',
                'Number of active connections',
                ['service'],
                registry=self.registry
            )
            
            self.memory_usage = Gauge(
                'memory_usage_bytes',
                'Memory usage in bytes',
                ['service'],
                registry=self.registry
            )
            
            logger.info(f"Prometheus metrics initialized for {self.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Prometheus metrics: {e}")
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code),
            service=self.service_name
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint,
            service=self.service_name
        ).observe(duration)
    
    def record_http_request(self, method: str, url: str, status_code: int, duration_ms: int, request_id: str):
        """Record HTTP request metrics (for shared client)."""
        # Extract endpoint from URL for cleaner metrics
        endpoint = url.split('?')[0].split('/')[-1] or 'root'
        
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code),
            service=self.service_name
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint,
            service=self.service_name
        ).observe(duration_ms / 1000.0)  # Convert ms to seconds
    
    def record_http_error(self, method: str, url: str, error_type: str, duration_ms: int, request_id: str):
        """Record HTTP error metrics."""
        endpoint = url.split('?')[0].split('/')[-1] or 'root'
        
        self.error_count.labels(
            error_type=f"http_{error_type}",
            service=self.service_name
        ).inc()
        
        # Also record as failed request
        self.request_count.labels(
            method=method,
            endpoint=endpoint,
            status_code="error",
            service=self.service_name
        ).inc()
    
    def record_pii_tokenize(self, scope: str, duration: float):
        """Record PII tokenization metrics."""
        self.pii_tokenize_count.labels(
            scope=scope,
            service=self.service_name
        ).inc()
        
        self.pii_tokenize_duration.labels(
            scope=scope,
            service=self.service_name
        ).observe(duration)
    
    def record_pii_detokenize(self, scope: str, duration: float):
        """Record PII detokenization metrics."""
        self.pii_detokenize_count.labels(
            scope=scope,
            service=self.service_name
        ).inc()
        
        self.pii_detokenize_duration.labels(
            scope=scope,
            service=self.service_name
        ).observe(duration)
    
    def record_lexnode_retrieve(self, duration: float, cache_hit: bool = False):
        """Record LexNode retrieval metrics."""
        self.lexnode_retrieve_count.labels(
            service=self.service_name
        ).inc()
        
        self.lexnode_retrieve_duration.labels(
            service=self.service_name
        ).observe(duration)
        
        if cache_hit:
            self.lexnode_cache_hits.labels(service=self.service_name).inc()
        else:
            self.lexnode_cache_misses.labels(service=self.service_name).inc()
    
    def record_intent_parse(self, duration: float, confidence: float):
        """Record intent parsing metrics."""
        self.intent_parse_count.labels(
            service=self.service_name
        ).inc()
        
        self.intent_parse_duration.labels(
            service=self.service_name
        ).observe(duration)
        
        self.intent_confidence.labels(
            service=self.service_name
        ).observe(confidence)
    
    def record_ai_draft_generation(self, duration: float, edit_rate: float):
        """Record AI draft generation metrics."""
        self.ai_draft_generation_count.labels(
            service=self.service_name
        ).inc()
        
        self.ai_draft_generation_duration.labels(
            service=self.service_name
        ).observe(duration)
        
        self.ai_draft_edit_rate.labels(
            service=self.service_name
        ).observe(edit_rate)
    
    def record_llm_request(self, provider: str, model: str, duration: float, tokens: Dict[str, int], cost: float):
        """Record LLM request metrics."""
        # Use existing AI draft generation metrics for now
        # In a full implementation, you'd want separate LLM metrics
        self.ai_draft_generation_count.labels(
            service=self.service_name
        ).inc()
        
        self.ai_draft_generation_duration.labels(
            service=self.service_name
        ).observe(duration)
    
    def record_document_finalization(self, duration: float):
        """Record document finalization metrics."""
        self.document_finalization_count.labels(
            service=self.service_name
        ).inc()
        
        self.document_finalization_duration.labels(
            service=self.service_name
        ).observe(duration)
    
    def record_error(self, error_type: str):
        """Record error metrics."""
        self.error_count.labels(
            error_type=error_type,
            service=self.service_name
        ).inc()
    
    def record_pii_leak_alert(self):
        """Record PII leak alert."""
        self.pii_leak_alerts.labels(
            service=self.service_name
        ).inc()
    
    def update_system_metrics(self, active_connections: int, memory_usage: int):
        """Update system metrics."""
        self.active_connections.labels(
            service=self.service_name
        ).set(active_connections)
        
        self.memory_usage.labels(
            service=self.service_name
        ).set(memory_usage)
    
    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        return generate_latest(self.registry).decode('utf-8')
    
    def get_content_type(self) -> str:
        """Get content type for metrics endpoint."""
        return CONTENT_TYPE_LATEST


# Global metrics collectors
_metrics_collectors: Dict[str, MetricsCollector] = {}


def get_metrics_collector(service_name: str) -> MetricsCollector:
    """Get or create a metrics collector for a service."""
    if service_name not in _metrics_collectors:
        _metrics_collectors[service_name] = MetricsCollector(service_name)
    return _metrics_collectors[service_name]


def record_request(service_name: str, method: str, endpoint: str, status_code: int, duration: float):
    """Record HTTP request metrics."""
    get_metrics_collector(service_name).record_request(method, endpoint, status_code, duration)


def record_pii_tokenize(service_name: str, scope: str, duration: float):
    """Record PII tokenization metrics."""
    get_metrics_collector(service_name).record_pii_tokenize(scope, duration)


def record_pii_detokenize(service_name: str, scope: str, duration: float):
    """Record PII detokenization metrics."""
    get_metrics_collector(service_name).record_pii_detokenize(scope, duration)


def record_lexnode_retrieve(service_name: str, duration: float, cache_hit: bool = False):
    """Record LexNode retrieval metrics."""
    get_metrics_collector(service_name).record_lexnode_retrieve(duration, cache_hit)


def record_intent_parse(service_name: str, duration: float, confidence: float):
    """Record intent parsing metrics."""
    get_metrics_collector(service_name).record_intent_parse(duration, confidence)


def record_ai_draft_generation(service_name: str, duration: float, edit_rate: float):
    """Record AI draft generation metrics."""
    get_metrics_collector(service_name).record_ai_draft_generation(duration, edit_rate)


def record_document_finalization(service_name: str, duration: float):
    """Record document finalization metrics."""
    get_metrics_collector(service_name).record_document_finalization(duration)


def record_error(service_name: str, error_type: str):
    """Record error metrics."""
    get_metrics_collector(service_name).record_error(error_type)


def record_pii_leak_alert(service_name: str):
    """Record PII leak alert."""
    get_metrics_collector(service_name).record_pii_leak_alert()


def update_system_metrics(service_name: str, active_connections: int, memory_usage: int):
    """Update system metrics."""
    get_metrics_collector(service_name).update_system_metrics(active_connections, memory_usage)


def setup_metrics(service_name: str):
    """Setup metrics for a service."""
    get_metrics_collector(service_name)
    logger.info(f"Metrics setup complete for {service_name}")