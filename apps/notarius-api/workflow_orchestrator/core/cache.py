"""
PII-safe caching utilities.
"""

from typing import Optional, Dict, Any
import hashlib


def get_cache_key(components: list) -> str:
    """
    Generate cache key from components.
    
    Args:
        components: List of string components
        
    Returns:
        Hexadecimal hash string
    """
    key_string = "|".join(str(c) for c in components)
    hash_obj = hashlib.sha256()
    hash_obj.update(key_string.encode('utf-8'))
    return hash_obj.hexdigest()

