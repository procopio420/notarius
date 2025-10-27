"""
PII Vault client for Intent Engine.
"""

from typing import Dict, Any, Optional
from uuid import UUID

from packages.observability import get_logger
from packages.core.http_client import get_http_client

logger = get_logger(__name__)


class PIIVaultClient:
    """Client for PII Vault service."""
    
    def __init__(self, base_url: str = "http://pii-vault:8000"):
        self.base_url = base_url
        self.http_client = get_http_client()
    
    async def tokenize(self, value: str, scope: str, tenant_id: UUID) -> Dict[str, Any]:
        """Tokenize a PII value."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/vault/tokenize",
                json={
                    "value": value,
                    "scope": scope,
                    "tenant_id": str(tenant_id),
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"PII tokenization failed: {e}")
            raise
    
    async def detokenize(self, token: str, tenant_id: UUID, purpose: str, actor_id: UUID = None) -> str:
        """Detokenize a PII token."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/vault/detokenize",
                json={
                    "token": token,
                    "tenant_id": str(tenant_id),
                    "purpose": purpose,
                    "actor_id": str(actor_id) if actor_id else None,
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["value"]
        except Exception as e:
            logger.error(f"PII detokenization failed: {e}")
            raise
    
    async def hash(self, value: str, tenant_id: UUID) -> str:
        """Generate hash for PII value."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/vault/hash",
                json={
                    "value": value,
                    "tenant_id": str(tenant_id),
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["hash"]
        except Exception as e:
            logger.error(f"PII hashing failed: {e}")
            raise


# Global PII Vault client instance
pii_vault_client: Optional[PIIVaultClient] = None


def get_pii_vault_client() -> PIIVaultClient:
    """Get the global PII Vault client instance."""
    if pii_vault_client is None:
        pii_vault_client = PIIVaultClient()
    return pii_vault_client
