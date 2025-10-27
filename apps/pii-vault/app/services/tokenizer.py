"""
PII tokenization service.
Generates deterministic tokens for PII values.
"""

import hashlib
import uuid
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TokenizerService:
    """Handles PII tokenization and detokenization."""
    
    def __init__(self):
        self.token_prefix = "PII_"
    
    def generate_token(self, pii_value: str, pii_type: str, tenant_id: str) -> str:
        """
        Generate deterministic token for PII value.
        
        The token is deterministic (same PII value always gets same token)
        but scoped to tenant for isolation.
        
        Args:
            pii_value: The PII value to tokenize
            pii_type: Type of PII (cpf, cnpj, nome, etc.)
            tenant_id: Tenant ID for scoping
            
        Returns:
            Deterministic token string
        """
        # Create deterministic hash
        hash_input = f"{tenant_id}:{pii_type}:{pii_value}"
        hash_value = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Generate token with prefix, type, and hash
        token = f"{self.token_prefix}{pii_type.upper()}_{hash_value[:16]}"
        
        return token
    
    def validate_token_format(self, token: str) -> bool:
        """
        Validate token format.
        
        Args:
            token: Token to validate
            
        Returns:
            True if valid format, False otherwise
        """
        if not token.startswith(self.token_prefix):
            return False
        
        # Token format: PII_TYPE_HASH
        parts = token.split('_', 2)
        if len(parts) != 3:
            return False
        
        # Validate hash length (should be 16 chars)
        hash_part = parts[2]
        if len(hash_part) != 16:
            return False
        
        # Validate hash is hexadecimal
        try:
            int(hash_part, 16)
            return True
        except ValueError:
            return False
    
    def extract_pii_type_from_token(self, token: str) -> Optional[str]:
        """
        Extract PII type from token.
        
        Args:
            token: Token to parse
            
        Returns:
            PII type or None if invalid
        """
        if not self.validate_token_format(token):
            return None
        
        parts = token.split('_', 2)
        return parts[1].lower()
    
    def generate_placeholder(self, pii_type: str, index: int = 0) -> str:
        """
        Generate placeholder for display (masks real value).
        
        Args:
            pii_type: Type of PII
            index: Index for multiple values of same type
            
        Returns:
            Placeholder string for display
        """
        placeholders = {
            "cpf": "***.***.***-**",
            "cnpj": "**.***.***/****-**",
            "nome": "[NOME_REDACTED]",
            "email": "[EMAIL_REDACTED]",
            "telefone": "(##) #####-####",
            "endereco": "[ENDERECO_REDACTED]",
            "rg": "[RG_REDACTED]",
            "data_nascimento": "##/##/####",
        }
        
        placeholder = placeholders.get(pii_type, f"[{pii_type.upper()}_REDACTED]")
        
        if index > 0:
            placeholder = f"{placeholder}_{index}"
        
        return placeholder

