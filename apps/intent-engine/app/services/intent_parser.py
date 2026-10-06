"""
Intent parsing service using NLP and AI.
"""

import json
import logging
import hashlib
import os
from typing import Dict, List, Optional

from .llm import get_llm_service

logger = logging.getLogger(__name__)


def hash_pii_for_cache(value: str, salt: Optional[str] = None) -> str:
    """
    Hash PII value for caching with salt.
    
    Args:
        value: PII value to hash
        salt: Optional salt (defaults to env var or default)
        
    Returns:
        Hashed value
    """
    if salt is None:
        salt = os.getenv("PII_HASH_SALT", "default_salt_change_in_production")
    
    # Use PBKDF2 for salted hashing
    return hashlib.pbkdf2_hmac(
        'sha256',
        value.encode('utf-8'),
        salt.encode('utf-8'),
        100000  # iterations
    ).hex()


def create_cache_key(data: Dict, include_pii: bool = False) -> str:
    """
    Create deterministic cache key from data.
    If include_pii is False, hash PII fields before creating key.
    
    Args:
        data: Data dict
        include_pii: Whether to include PII in key (should be False for caching)
        
    Returns:
        Cache key string
    """
    # PII fields to hash
    pii_fields = ['cpf', 'cnpj', 'rg', 'endereco', 'matricula', 'nome', 'email', 'phone']
    
    # Create a normalized copy
    normalized = {}
    for key, value in data.items():
        key_lower = key.lower()
        
        # Hash PII fields
        if not include_pii and any(pii_field in key_lower for pii_field in pii_fields):
            if isinstance(value, str) and value:
                normalized[key] = hash_pii_for_cache(value)
            elif isinstance(value, dict):
                # Recursively hash nested PII
                normalized[key] = create_cache_key(value, include_pii=False)
            else:
                normalized[key] = value
        else:
            normalized[key] = value
    
    # Create deterministic hash of normalized data
    data_str = json.dumps(normalized, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()


class IntentParser:
    """Parse natural language intents into structured data."""
    
    def __init__(self):
        self.supported_document_types = [
            "procuracao",
            "certidao",
            "testamento",
            "escritura",
            "contrato",
        ]
        
        self.supported_actions = [
            "create",
            "modify",
            "revoke",
            "cancel",
        ]
    
    async def parse_intent(
        self,
        intent_text: str,
        context: Optional[Dict] = None,
        tenant_id: Optional[str] = None
    ) -> Dict:
        """
        Parse natural language intent.
        
        Args:
            intent_text: Natural language command in Portuguese
            context: Additional context (processo_id, tenant info, etc.)
            
        Returns:
            Structured intent with action, document_type, entities, confidence
        """
        logger.info(f"Parsing intent: {intent_text[:100]}...")
        
        # Build prompt for OpenAI
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(intent_text, context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            # Call LLM service
            llm_service = get_llm_service()
            # Convert tenant_id to UUID if provided
            from uuid import UUID
            tenant_uuid = None
            if tenant_id:
                try:
                    tenant_uuid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
                except (ValueError, TypeError):
                    tenant_uuid = None
            elif context and 'tenant_id' in context:
                try:
                    tenant_uuid = UUID(context['tenant_id']) if isinstance(context['tenant_id'], str) else context['tenant_id']
                except (ValueError, TypeError):
                    tenant_uuid = None
            
            response = await llm_service.chat_completion(
                messages=messages,
                model="gpt-4o-mini",
                temperature=0.3,  # Low temperature for consistency
                max_tokens=1000,
                tenant_id=tenant_uuid,
            )
            
            # Parse JSON response
            parsed_intent = json.loads(response)
            
            # Add metadata
            parsed_intent["original_intent"] = intent_text
            parsed_intent["context"] = context or {}
            
            logger.info(f"Parsed intent: action={parsed_intent.get('action')}, doc_type={parsed_intent.get('document_type')}")
            
            return parsed_intent
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # Return low-confidence fallback
            return self._create_fallback_intent(intent_text, context)
        except Exception as e:
            logger.error(f"Intent parsing failed: {e}", exc_info=True)
            raise
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for intent parsing."""
        return f"""You are an expert Brazilian legal document assistant.
        
Your job is to parse natural language commands in Portuguese and extract structured information for creating notary documents.

Supported document types: {', '.join(self.supported_document_types)}
Supported actions: {', '.join(self.supported_actions)}

Output format (JSON only, no explanation):
{{
    "action": "create|modify|revoke|cancel",
    "document_type": "procuracao|certidao|testamento|escritura|contrato",
    "confidence": 0.0-1.0,
    "entities": {{
        "outorgante": "person granting power",
        "outorgado": "person receiving power",
        "objeto": "what the document is about",
        "valor": "monetary value if applicable",
        "imovel": "property description if applicable",
        ...other relevant entities...
    }},
    "pii_fields": ["nome", "cpf", "cnpj", "endereco", ...],
    "suggestions": ["list of suggestions for improving the intent"]
}}

Be precise and extract all relevant legal entities from the Portuguese text."""
    
    def _build_user_prompt(self, intent_text: str, context: Optional[Dict]) -> str:
        """Build user prompt with intent and context."""
        prompt = f"Parse this intent:\n\n{intent_text}"
        
        if context:
            prompt += f"\n\nContext: {json.dumps(context, ensure_ascii=False)}"
        
        return prompt
    
    def _create_fallback_intent(self, intent_text: str, context: Optional[Dict]) -> Dict:
        """Create low-confidence fallback intent."""
        return {
            "action": "create",
            "document_type": "procuracao",  # Default
            "confidence": 0.2,
            "entities": {},
            "pii_fields": [],
            "suggestions": ["Unable to parse intent accurately - please provide more details"],
            "original_intent": intent_text,
            "context": context or {},
            "fallback": True
        }
    
    async def validate_intent(
        self,
        intent_text: str,
        document_type: str
    ) -> Dict:
        """
        Validate if intent matches expected document type.
        
        Args:
            intent_text: Natural language intent
            document_type: Expected document type
            
        Returns:
            Validation result with is_valid, confidence, errors, suggestions
        """
        logger.info(f"Validating intent for document type: {document_type}")
        
        system_prompt = f"""You are validating if a natural language intent is appropriate for creating a {document_type}.

Analyze the intent and return JSON:
{{
    "is_valid": true|false,
    "confidence": 0.0-1.0,
    "errors": ["list of errors if any"],
    "suggestions": ["list of suggestions for improvement"],
    "missing_info": ["list of missing required information"]
}}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Intent: {intent_text}\nDocument type: {document_type}"},
        ]
        
        try:
            llm_service = get_llm_service()
            response = await llm_service.chat_completion(messages=messages, temperature=0.2)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Intent validation failed: {e}")
            return {
                "is_valid": False,
                "confidence": 0.0,
                "errors": [str(e)],
                "suggestions": [],
                "missing_info": []
            }

