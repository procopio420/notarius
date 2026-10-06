"""
PII (Personally Identifiable Information) utilities.

Provides hashing and redaction functions to ensure PII is never exposed
in logs, metrics, or cache.
"""

import hashlib
import os
from typing import Dict, Any, List
from workflow_orchestrator.models.contracts import DocumentoBasico


def hash_pii(value: str, salt_env: str = "NOTARIUS_SALT") -> str:
    """
    Hash PII value using SHA256 with salt.
    
    Args:
        value: PII value to hash (CPF, CNPJ, etc.)
        salt_env: Environment variable name containing the salt
        
    Returns:
        Hexadecimal hash string
    """
    if not value:
        return ""
    
    # Get salt from environment or use default
    salt = os.getenv(salt_env, "notarius_default_salt_change_in_production")
    
    # Normalize value (remove formatting)
    normalized = "".join(filter(str.isalnum, value))
    
    # Hash with salt
    hash_obj = hashlib.sha256()
    hash_obj.update(salt.encode('utf-8'))
    hash_obj.update(normalized.encode('utf-8'))
    
    return hash_obj.hexdigest()


def redact_pii_in_logs(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove PII from dictionary for logging.
    
    Args:
        data: Dictionary that may contain PII
        
    Returns:
        Dictionary with PII fields redacted
    """
    redacted = data.copy()
    
    # Fields that may contain PII
    pii_fields = [
        "cpf_cnpj",
        "cpf",
        "cnpj",
        "nome",
        "email",
        "endereco",
        "endereço",
        "telefone",
        "rg",
        "matricula",
        "matrícula",
    ]
    
    def redact_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, value in d.items():
            if key.lower() in pii_fields:
                result[key] = "[REDACTED]"
            elif isinstance(value, dict):
                result[key] = redact_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    redact_dict(item) if isinstance(item, dict) else "[REDACTED]" if isinstance(item, str) and any(field in key.lower() for field in pii_fields) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    
    return redact_dict(redacted)


def generate_cache_key(doc: DocumentoBasico, anexos: List[str]) -> str:
    """
    Generate stable cache key from document data using hashed PII.
    
    Args:
        doc: DocumentoBasico instance
        anexos: List of attachment identifiers
        
    Returns:
        Stable cache key (same input = same key)
    """
    import hashlib
    
    # Build components for cache key (no raw PII)
    components = [
        doc.tipo_documento,
        doc.especialidade,
        doc.uf,
        doc.municipio or "",
    ]
    
    # Add hashed PII from partes
    for parte in doc.partes:
        if parte.cpf_cnpj:
            components.append(hash_pii(parte.cpf_cnpj))
        components.append(parte.papel)
    
    # Add anexos (sorted for stability)
    components.extend(sorted(anexos))
    
    # Generate hash
    key_string = "|".join(components)
    hash_obj = hashlib.sha256()
    hash_obj.update(key_string.encode('utf-8'))
    
    return hash_obj.hexdigest()

