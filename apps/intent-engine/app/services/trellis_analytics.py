"""TRELLIS analytics service for data-driven optimization."""

import os
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from packages.core.http_client import get_http_client
from packages.observability import get_logger

logger = get_logger(__name__)

class TRELLISAnalyticsService:
    """Service for logging and analyzing TRELLIS interactions."""
    
    def __init__(self):
        self.notarius_api_url = os.getenv("NOTARIUS_API_URL", "http://notarius-api:8000")
        self.http_client = None
    
    async def init(self):
        """Initialize HTTP client."""
        self.http_client = get_http_client()
    
    async def log_interaction(
        self,
        user_id: str,
        session_id: str,
        original_command: str,
        intent: 'Intent',
        cluster: Optional['TRELLISCluster'],
        processing_time_ms: int,
        success: bool,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        """Log TRELLIS interaction to Django backend."""
        log_data = {
            "user_id": user_id,
            "session_id": session_id,
            "original_command": original_command,
            "parsed_intent": intent.dict(),
            "matched_cluster": cluster.id if cluster else None,
            "cluster_confidence": cluster.confidence if cluster else 0.0,
            "used_deterministic_parser": cluster is not None,
            "used_llm_fallback": cluster is None,
            "processing_time_ms": processing_time_ms,
            "llm_tokens_used": intent.metadata.get("llm_tokens", 0),
            "llm_cost_usd": intent.metadata.get("llm_cost_usd", 0),
            "success": success,
            "error_type": error_type,
            "error_message": error_message,
        }
        
        try:
            response = await self.http_client.post(
                f"{self.notarius_api_url}/api/v1/trellis/log-interaction/",
                json=log_data
            )
            response.raise_for_status()
            logger.info("TRELLIS interaction logged", interaction_id=response.json()["interaction_id"])
        except Exception as e:
            logger.error("Failed to log TRELLIS interaction", error=str(e))
    
    async def update_user_feedback(
        self,
        interaction_id: str,
        accepted: bool,
        edited: bool,
        sentiment_score: Optional[float] = None,
        feedback_text: Optional[str] = None
    ):
        """Update interaction with user feedback."""
        feedback_data = {
            "user_accepted": accepted,
            "user_edited": edited,
            "sentiment_score": sentiment_score,
            "user_feedback_text": feedback_text
        }
        
        try:
            await self.http_client.patch(
                f"{self.notarius_api_url}/api/v1/trellis/interactions/{interaction_id}/feedback/",
                json=feedback_data
            )
            logger.info("User feedback recorded", interaction_id=interaction_id)
        except Exception as e:
            logger.error("Failed to update feedback", error=str(e))
    
    async def get_cluster_metrics(self) -> List[Dict[str, Any]]:
        """Fetch cluster metrics for prioritization."""
        try:
            response = await self.http_client.get(
                f"{self.notarius_api_url}/api/v1/trellis/cluster-metrics/"
            )
            response.raise_for_status()
            return response.json()["metrics"]
        except Exception as e:
            logger.error("Failed to fetch cluster metrics", error=str(e))
            return []
