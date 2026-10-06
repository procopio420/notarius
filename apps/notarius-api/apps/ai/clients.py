"""
Integration clients for AI services (PII Vault, Intent Engine, LexNode).
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID

import httpx
from django.conf import settings

# Ensure packages directory is in Python path
# This is a safeguard in case Django hasn't loaded it yet
def _setup_packages_path():
    """Set up packages directory in Python path."""
    # Check Docker mount point first - need to add parent of /packages (which is /)
    # so that 'packages' can be imported as a package
    if os.path.exists('/packages'):
        # Add root directory so packages can be imported
        if '/' not in sys.path:
            sys.path.insert(0, '/')
        # Also ensure /packages itself is not in path (would cause conflicts)
        if '/packages' in sys.path:
            sys.path.remove('/packages')
        return
    
    # Check if we can already import packages
    try:
        import packages
        return
    except ImportError:
        pass
    
    # Try to find packages directory relative to this file
    current_file = Path(__file__).resolve()
    # Go up: ai -> apps -> notarius-api -> apps -> project root
    project_root = current_file.parent.parent.parent.parent.parent
    packages_path = project_root / 'packages'
    if packages_path.exists():
        # Add project root to path so packages can be imported
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

_setup_packages_path()

# Import http_client with fallback for build time
try:
    from packages.core.http_client import get_http_client, init_http_client
    # Store the init function for lazy initialization
    _init_http_client_func = init_http_client
except ImportError as e:
    _init_http_client_func = None
    # During Docker build or if packages aren't available, create a lazy loader
    _http_client_import_error = e
    
    def get_http_client():
        """Lazy-load HTTP client. Re-attempts import at runtime with path setup."""
        # Ensure packages directory is in Python path before importing
        _setup_packages_path()
        
        # Try multiple import strategies
        try:
            # Strategy 1: Standard import
            from packages.core.http_client import get_http_client as _get_http_client, init_http_client as _init_http_client
            # Try to get the client, initialize if needed
            try:
                return _get_http_client()
            except RuntimeError as e:
                if "not initialized" in str(e):
                    # Initialize the HTTP client synchronously
                    import asyncio
                    try:
                        # Try to get existing event loop
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # If loop is running, we can't use it - create a new one
                            # This shouldn't happen in Django views, but handle it
                            asyncio.run(_init_http_client(service_name="notarius-api"))
                        else:
                            loop.run_until_complete(_init_http_client(service_name="notarius-api"))
                    except RuntimeError:
                        # No event loop, create one
                        asyncio.run(_init_http_client(service_name="notarius-api"))
                    return _get_http_client()
                raise
        except ImportError:
            try:
                # Strategy 2: If /packages is in path, try direct import
                import importlib.util
                if os.path.exists('/packages/core/http_client.py'):
                    spec = importlib.util.spec_from_file_location(
                        "packages.core.http_client",
                        "/packages/core/http_client.py"
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        # Add parent to sys.path temporarily for relative imports
                        if '/' not in sys.path:
                            sys.path.insert(0, '/')
                        spec.loader.exec_module(module)
                        client = module.get_http_client()
                        # Initialize if needed
                        try:
                            return client
                        except RuntimeError as e:
                            if "not initialized" in str(e):
                                import asyncio
                                asyncio.run(module.init_http_client(service_name="notarius-api"))
                                return module.get_http_client()
                        return client
            except Exception:
                pass
            
            # Strategy 3: Try adding parent directory and importing
            try:
                if os.path.exists('/packages') and '/' not in sys.path:
                    sys.path.insert(0, '/')
                    from packages.core.http_client import get_http_client as _get_http_client, init_http_client as _init_http_client
                    try:
                        return _get_http_client()
                    except RuntimeError as e:
                        if "not initialized" in str(e):
                            import asyncio
                            asyncio.run(_init_http_client(service_name="notarius-api"))
                            return _get_http_client()
                        raise
            except ImportError:
                pass
            
            # All strategies failed
            raise RuntimeError(
                f"HTTP client not available. Packages not found. "
                f"Original error: {_http_client_import_error}. "
                f"Make sure packages directory is in Python path. "
                f"Current sys.path: {sys.path[:5]}. "
                f"/packages exists: {os.path.exists('/packages')}. "
                f"/packages/core/http_client.py exists: {os.path.exists('/packages/core/http_client.py') if os.path.exists('/packages') else False}"
            ) from _http_client_import_error

logger = logging.getLogger(__name__)


class PIIVaultClient:
    """Client for PII Vault service."""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or getattr(settings, 'PII_VAULT_URL', 'http://pii-vault:8000')
        self._http_client = None
    
    def _ensure_http_client_initialized(self):
        """Ensure HTTP client is initialized, handling both sync and async contexts."""
        if self._http_client is None:
            try:
                self._http_client = get_http_client()
            except RuntimeError as e:
                if "not initialized" in str(e) and _init_http_client_func:
                    # Initialize the HTTP client if not initialized
                    import asyncio
                    import concurrent.futures
                    
                    try:
                        # Check if we're in a running event loop
                        loop = asyncio.get_running_loop()
                        # We're in an async context - can't use asyncio.run()
                        # Use a thread to run the initialization
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                asyncio.run,
                                _init_http_client_func(service_name="notarius-api")
                            )
                            future.result(timeout=10)  # Wait for initialization
                    except RuntimeError:
                        # No running loop - we can use asyncio.run() or get_event_loop()
                        try:
                            asyncio.run(_init_http_client_func(service_name="notarius-api"))
                        except RuntimeError:
                            # Try with existing event loop
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    # Running loop - use thread
                                    with concurrent.futures.ThreadPoolExecutor() as executor:
                                        future = executor.submit(
                                            asyncio.run,
                                            _init_http_client_func(service_name="notarius-api")
                                        )
                                        future.result(timeout=10)
                                else:
                                    loop.run_until_complete(_init_http_client_func(service_name="notarius-api"))
                            except RuntimeError:
                                # Last resort - use thread
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(
                                        asyncio.run,
                                        _init_http_client_func(service_name="notarius-api")
                                    )
                                    future.result(timeout=10)
                    self._http_client = get_http_client()
                else:
                    raise
    
    @property
    def http_client(self):
        """Lazy-load HTTP client when needed."""
        self._ensure_http_client_initialized()
        return self._http_client
    
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
        self._http_client = None
    
    def _ensure_http_client_initialized(self):
        """Ensure HTTP client is initialized, handling both sync and async contexts."""
        if self._http_client is None:
            try:
                self._http_client = get_http_client()
            except RuntimeError as e:
                if "not initialized" in str(e) and _init_http_client_func:
                    # Initialize the HTTP client if not initialized
                    import asyncio
                    import concurrent.futures
                    
                    try:
                        # Check if we're in a running event loop
                        loop = asyncio.get_running_loop()
                        # We're in an async context - can't use asyncio.run()
                        # Use a thread to run the initialization
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                asyncio.run,
                                _init_http_client_func(service_name="notarius-api")
                            )
                            future.result(timeout=10)  # Wait for initialization
                    except RuntimeError:
                        # No running loop - we can use asyncio.run() or get_event_loop()
                        try:
                            asyncio.run(_init_http_client_func(service_name="notarius-api"))
                        except RuntimeError:
                            # Try with existing event loop
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    # Running loop - use thread
                                    with concurrent.futures.ThreadPoolExecutor() as executor:
                                        future = executor.submit(
                                            asyncio.run,
                                            _init_http_client_func(service_name="notarius-api")
                                        )
                                        future.result(timeout=10)
                                else:
                                    loop.run_until_complete(_init_http_client_func(service_name="notarius-api"))
                            except RuntimeError:
                                # Last resort - use thread
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(
                                        asyncio.run,
                                        _init_http_client_func(service_name="notarius-api")
                                    )
                                    future.result(timeout=10)
                    self._http_client = get_http_client()
                else:
                    raise
    
    @property
    def http_client(self):
        """Lazy-load HTTP client when needed."""
        self._ensure_http_client_initialized()
        return self._http_client
    
    async def parse_intent(self, intent: str, processo_id: UUID, tenant_id: UUID, user_id: Optional[UUID]) -> Dict[str, Any]:
        """Parse natural language intent into structured data."""
        try:
            response = await self.http_client.post(
                f"{self.base_url}/api/v1/parse-intent",
                json={
                    "intent": intent,
                    "processo_id": str(processo_id) if processo_id else None,
                    "tenant_id": str(tenant_id),
                    "user_id": str(user_id) if user_id else None,
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
        self._http_client = None
    
    def _ensure_http_client_initialized(self):
        """Ensure HTTP client is initialized, handling both sync and async contexts."""
        if self._http_client is None:
            try:
                self._http_client = get_http_client()
            except RuntimeError as e:
                if "not initialized" in str(e) and _init_http_client_func:
                    # Initialize the HTTP client if not initialized
                    import asyncio
                    import concurrent.futures
                    
                    try:
                        # Check if we're in a running event loop
                        loop = asyncio.get_running_loop()
                        # We're in an async context - can't use asyncio.run()
                        # Use a thread to run the initialization
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(
                                asyncio.run,
                                _init_http_client_func(service_name="notarius-api")
                            )
                            future.result(timeout=10)  # Wait for initialization
                    except RuntimeError:
                        # No running loop - we can use asyncio.run() or get_event_loop()
                        try:
                            asyncio.run(_init_http_client_func(service_name="notarius-api"))
                        except RuntimeError:
                            # Try with existing event loop
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    # Running loop - use thread
                                    with concurrent.futures.ThreadPoolExecutor() as executor:
                                        future = executor.submit(
                                            asyncio.run,
                                            _init_http_client_func(service_name="notarius-api")
                                        )
                                        future.result(timeout=10)
                                else:
                                    loop.run_until_complete(_init_http_client_func(service_name="notarius-api"))
                            except RuntimeError:
                                # Last resort - use thread
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(
                                        asyncio.run,
                                        _init_http_client_func(service_name="notarius-api")
                                    )
                                    future.result(timeout=10)
                    self._http_client = get_http_client()
                else:
                    raise
    
    @property
    def http_client(self):
        """Lazy-load HTTP client when needed."""
        self._ensure_http_client_initialized()
        return self._http_client
    
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
        user_id: Optional[UUID],
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
            
            # 4. Prepare variaveis_json from pii_tokens
            variaveis_json = {}
            if pii_tokens and isinstance(pii_tokens, list):
                for token in pii_tokens:
                    if isinstance(token, dict) and 'entity' in token and 'token' in token:
                        entity_type = token.get('entity', {}).get('type')
                        token_value = token.get('token')
                        if entity_type and token_value:
                            variaveis_json[entity_type] = token_value
            
            # 5. Prepare minuta data
            minuta_data = {
                'processo_id': processo_id,
                'versao': 1,
                'gerada_por': 'ia',
                'status': 'rascunho',
                'corpo_md': draft_result.get('content', ''),
                'variaveis_json': variaveis_json,
                'citations': draft_result.get('citations', []),
                'grounding_confidence': draft_result.get('grounding_confidence', draft_result.get('confidence', 0.0)),
                'skeleton_cache_key': draft_result.get('cache_key', ''),
                'template_version': '1.0',
                'lexnode_trace': draft_result.get('trace', {}),
                'parsed_intent': intent_result.get('parsed_intent', {}),
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
