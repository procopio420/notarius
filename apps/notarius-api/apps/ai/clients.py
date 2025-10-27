"""
Integration clients for AI services (PII Vault, Intent Engine, LexNode).
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

import httpx
from django.conf import settings
from packages.core.http_client import get_http_client

logger = logging.getLogger(__name__)


class PIIVaultClient:
    """Client for PII Vault service."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or getattr(settings, 'PII_VAULT_URL', 'http://pii-vault:8000')
        self.http_client = get_http_client()
    
    async def store_pii(self, pii_value: str, pii_type: str, tenant_id: UUID, user_id: UUID = None) -> Dict[str, Any]:
        """Store PII and get token."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/store-pii",
                json={
                    "pii_value": pii_value,
                    "pii_type": pii_type,
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id) if user_id else None,
                }
            )
            response.raise_for_status()
            return response.json()  # Returns {record_id, token, hash, reused}
        except Exception as e:
            logger.error(f"PII storage failed: {e}")
            raise
    
    async def tokenize(self, pii_data: Dict[str, str], tenant_id: UUID, user_id: UUID = None) -> Dict[str, str]:
        """Tokenize multiple PII values."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/tokenize",
                json={
                    "pii_data": pii_data,
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id) if user_id else None,
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["tokens"]  # Returns {pii_type: token}
        except Exception as e:
            logger.error(f"PII tokenization failed: {e}")
            raise
    
    async def retrieve_pii(self, token: str, tenant_id: UUID) -> Optional[str]:
        """Retrieve PII value by token."""
        try:
            logger.debug(f"Retrieving PII for token {token[:10]}... from {self.base_url}")
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/retrieve-pii",
                json={
                    "token": token,
                    "tenant_id": str(tenant_id),
                }
            )
            response.raise_for_status()
            result = response.json()
            return result.get("pii_value")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"PII token not found: {token[:10]}...")
                return None
            logger.error(f"PII retrieval HTTP error {e.response.status_code}: {e}")
            return None  # Return None instead of raising to prevent hanging
        except httpx.ConnectError as e:
            logger.error(f"PII Vault service unavailable at {self.base_url}: {e}")
            return None  # Return None instead of raising to prevent hanging
        except httpx.TimeoutException as e:
            logger.error(f"PII retrieval timeout for token {token[:10]}...: {e}")
            return None  # Return None instead of raising to prevent hanging
        except Exception as e:
            logger.error(f"PII retrieval failed for token {token[:10]}...: {e}")
            return None  # Return None instead of raising to prevent hanging
    
    async def detokenize(self, tokens: Dict[str, str], tenant_id: UUID) -> Dict[str, Optional[str]]:
        """Detokenize multiple tokens."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/detokenize",
                json={
                    "tokens": tokens,
                    "tenant_id": str(tenant_id),
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["pii_data"]
        except Exception as e:
            logger.error(f"PII detokenization failed: {e}")
            raise
    
    async def batch_tokenize(self, pii_data: List[Dict[str, Any]], tenant_id: UUID) -> List[Dict[str, Any]]:
        """Batch tokenize multiple PII values."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/vault/batch-tokenize",
                json={
                    "values": [
                        {
                            "value": item["value"],
                            "scope": item["scope"],
                            "tenant_id": str(tenant_id),
                        }
                        for item in pii_data
                    ]
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["tokens"]
        except Exception as e:
            logger.error(f"Batch PII tokenization failed: {e}")
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


class IntentEngineClient:
    """Client for Intent Engine service."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or getattr(settings, 'INTENT_ENGINE_URL', 'http://intent-engine:8000')
        self.http_client = get_http_client()
    
    async def parse_intent(self, intent: str, processo_id: UUID, tenant_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Parse natural language intent into structured data."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/parse-intent",
                json={
                    "intent": intent,
                    "processo_id": str(processo_id) if processo_id else None,
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id),
                }
            )
            response.raise_for_status()
            return response.json()  # Returns {intent_id, parsed_intent, confidence, suggestions}
        except Exception as e:
            logger.error(f"Intent parsing failed: {e}")
            raise
    
    async def generate_draft(self, parsed_intent: Dict, template_content: str = None, legal_citations: List[Dict] = None, tenant_id: UUID = None, user_id: UUID = None) -> Dict[str, Any]:
        """Generate legal draft from parsed intent."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/generate-draft",
                json={
                    "parsed_intent": parsed_intent,
                    "template_content": template_content,
                    "legal_citations": legal_citations or [],
                    "tenant_id": str(tenant_id) if tenant_id else None,
                    "user_id": str(user_id) if user_id else None,
                }
            )
            response.raise_for_status()
            return response.json()  # Returns {draft_id, content, placeholders, citations, grounding_confidence, metadata}
        except Exception as e:
            logger.error(f"Draft generation failed: {e}")
            raise
    
    async def rewrite_content(
        self, 
        content: str, 
        improvement_prompt: str,
        document_type: str,
        preserve_variables: bool = True,
        tenant_id: UUID = None,
        user_id: UUID = None
    ) -> Dict[str, Any]:
        """Rewrite document content using AI.
        
        NOTE: This endpoint needs to be implemented in the Intent Engine service.
        Currently, the backend uses a rule-based fallback implementation.
        """
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/rewrite-content",
                json={
                    "content": content,
                    "improvement_prompt": improvement_prompt,
                    "document_type": document_type,
                    "preserve_variables": preserve_variables,
                    "tenant_id": str(tenant_id) if tenant_id else None,
                    "user_id": str(user_id) if user_id else None,
                }
            )
            response.raise_for_status()
            return response.json()  # Returns {rewritten_content, confidence, tokens_used}
        except Exception as e:
            logger.error(f"Content rewriting failed: {e}")
            raise
    
    async def extract_pii(self, text: str, pii_types: List[str] = None) -> Dict[str, List[str]]:
        """Extract PII from text."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/extract-pii",
                json={
                    "text": text,
                    "pii_types": pii_types,
                }
            )
            response.raise_for_status()
            result = response.json()
            return result["extracted_pii"]
        except Exception as e:
            logger.error(f"PII extraction failed: {e}")
            raise


class LexNodeClient:
    """Client for LexNode RAG service."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or getattr(settings, 'LEXNODE_URL', 'http://lexnode-api:8000')
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
    
    async def retrieve_template(
        self, 
        document_type: str, 
        jurisdiction: str,
        constraints: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve template for document type and jurisdiction."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/lexnode/retrieve-template",
                json={
                    "document_type": document_type,
                    "jurisdiction": jurisdiction,
                    "constraints": constraints or {},
                    "limit": 1,  # Get the best match
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Return the first template if found
            if result.get("templates") and len(result["templates"]) > 0:
                return result["templates"][0]
            return None
            
        except Exception as e:
            logger.error(f"LexNode template retrieval failed: {e}")
            return None


class AIServiceManager:
    """Manager for all AI services with error handling and retries."""
    
    def __init__(self):
        self.pii_vault = PIIVaultClient()
        self.intent_engine = IntentEngineClient()
        self.lexnode = LexNodeClient()
    
    async def generate_minuta_from_intent(
        self, 
        command: str, 
        tenant_id: UUID, 
        user_id: UUID,
        processo_id: UUID
    ) -> Dict[str, Any]:
        """
        Complete workflow: parse intent → tokenize PII → generate draft.
        
        Args:
            command: Natural language command
            tenant_id: Tenant ID
            user_id: User ID for audit
            processo_id: Process ID
            
        Returns:
            Dict with minuta data ready for database storage
        """
        try:
            # 1. Parse intent
            logger.info(f"Parsing intent for command: {command[:50]}...")
            intent_result = await self.intent_engine.parse_intent(command, processo_id, tenant_id, user_id)
            
            # 2. Tokenize PII entities
            pii_entities = intent_result.get('parsed_intent', {}).get('pii_entities', [])
            logger.info(f"Tokenizing {len(pii_entities)} PII entities")
            pii_tokens = intent_result.get('pii_tokens', [])
            
            # 3. Generate draft
            logger.info("Generating legal draft")
            draft_result = await self.intent_engine.generate_draft(
                parsed_intent=intent_result['parsed_intent'],
                template_content=None,
                legal_citations=[],
                tenant_id=tenant_id,
                user_id=user_id
            )
            
            # 4. Prepare minuta data
            minuta_data = {
                'processo_id': processo_id,
                'versao': 1,
                'gerada_por': 'ia',
                'status': 'rascunho',
                'corpo_md': draft_result.get('content', ''),
                'variaveis_json': {token['entity']['type']: token['token'] for token in pii_tokens},
                'citations': draft_result.get('citations', []),
                'grounding_confidence': draft_result.get('confidence', 0.0),
                'skeleton_cache_key': draft_result.get('cache_key', ''),
                'template_version': '1.0',
                'lexnode_trace': draft_result.get('trace', {}),
            }
            
            logger.info(f"Successfully generated minuta with confidence: {draft_result.get('confidence', 0.0):.2f}")
            return minuta_data
            
        except Exception as e:
            logger.error(f"Failed to generate minuta from intent: {e}")
            raise
    
    async def finalize_minuta(self, minuta_id: UUID, tenant_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """
        Finalize minuta by detokenizing PII and generating final document.
        
        Args:
            minuta_id: Minuta ID
            tenant_id: Tenant ID
            user_id: User ID for audit
            
        Returns:
            Dict with final document data
        """
        try:
            from apps.documentos.finalizer import get_document_finalizer
            
            logger.info(f"Finalizing minuta {minuta_id}")
            
            # Use the document finalizer service
            finalizer = get_document_finalizer()
            final_document_data = await finalizer.finalize_minuta(
                minuta_id=minuta_id,
                tenant_id=tenant_id,
                user_id=user_id
            )
            
            logger.info(f"Successfully finalized minuta {minuta_id}")
            return final_document_data
            
        except Exception as e:
            logger.error(f"Failed to finalize minuta {minuta_id}: {e}")
            raise
    
    async def rewrite_document_content(
        self,
        content: str,
        improvement_prompt: str,
        document_type: str,
        preserve_variables: bool = True,
        tenant_id: UUID = None,
        user_id: UUID = None
    ) -> Dict[str, Any]:
        """Rewrite document content with AI."""
        try:
            result = await self.intent_engine.rewrite_content(
                content=content,
                improvement_prompt=improvement_prompt,
                document_type=document_type,
                preserve_variables=preserve_variables,
                tenant_id=tenant_id,
                user_id=user_id
            )
            return result
        except Exception as e:
            logger.error(f"Document rewriting failed: {e}")
            raise


# Global instance
ai_service_manager = AIServiceManager()


def get_ai_service_manager() -> AIServiceManager:
    """Get the global AI service manager instance."""
    return ai_service_manager
