"""
LexNode client for Intent Engine.
"""

from typing import Dict, Any, List, Optional

from packages.observability import get_logger
from packages.core.http_client import get_http_client

logger = get_logger(__name__)


class LexNodeClient:
    """Client for LexNode RAG service."""
    
    def __init__(self, base_url: str = "http://lexnode-api:8000"):
        self.base_url = base_url
        self.http_client = get_http_client()
    
    async def retrieve(self, query: str, constraints: Dict[str, Any] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Retrieve legal documents."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/lexnode/retrieve",
                json={
                    "query": query,
                    "constraints": constraints or {},
                    "top_k": top_k,
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["hits"]
        except Exception as e:
            logger.error(f"LexNode retrieval failed: {e}")
            raise
    
    async def generate_grounded_draft(self, act_type: str, variables: Dict[str, Any], constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate grounded legal draft."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/lexnode/grounded-draft",
                json={
                    "act_type": act_type,
                    "variables": variables,
                    "constraints": constraints or {},
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"LexNode grounded draft generation failed: {e}")
            raise


# Global LexNode client instance
lexnode_client: Optional[LexNodeClient] = None


def get_lexnode_client() -> LexNodeClient:
    """Get the global LexNode client instance."""
    if lexnode_client is None:
        lexnode_client = LexNodeClient()
    return lexnode_client
