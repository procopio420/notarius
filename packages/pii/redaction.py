"""
PII redaction utilities for logs and vector stores.
"""

import re
import logging
from typing import List, Dict, Optional
from packages.core.models import PIIEntity, PIIEntityType
from packages.pii.extractors import MultiLayerPIIExtractor

logger = logging.getLogger(__name__)


class LogSanitizer:
    """Sanitizes log messages to remove PII."""
    
    def __init__(self):
        self.extractor = MultiLayerPIIExtractor()
        self.pii_patterns = [
            (r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', '[CPF]'),  # CPF formatted
            (r'\b\d{11}\b', '[CPF]'),  # CPF unformatted (context-dependent)
            (r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', '[CNPJ]'),  # CNPJ formatted
            (r'\b\d{14}\b', '[CNPJ]'),  # CNPJ unformatted (context-dependent)
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
            (r'\b\(\d{2}\)\s?\d{4,5}-?\d{4}\b', '[PHONE]'),
            (r'\b\d{2}\s?\d{4,5}-?\d{4}\b', '[PHONE]'),
        ]
    
    def sanitize(self, text: str) -> str:
        """
        Sanitize text by replacing PII with placeholders.
        
        Args:
            text: Text potentially containing PII
            
        Returns:
            Sanitized text with PII replaced by placeholders
        """
        sanitized = text
        
        for pattern, replacement in self.pii_patterns:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
        
        return sanitized


class PIIRedactionMiddleware:
    """Middleware for automatic PII redaction in logs."""
    
    def __init__(self):
        self.sanitizer = LogSanitizer()
    
    def redact_log_message(self, message: str) -> str:
        """Redact PII from log message."""
        return self.sanitizer.sanitize(message)


class PIILeakDetector:
    """Detects potential PII leaks in text."""
    
    def __init__(self):
        self.extractor = MultiLayerPIIExtractor()
    
    async def detect_leaks(self, text: str) -> List[PIIEntity]:
        """Detect PII entities in text."""
        try:
            entities = await self.extractor.extract(text)
            return entities
        except Exception as e:
            logger.warning(f"Failed to detect PII leaks: {e}")
            return []


def redact_pii_from_content(content: str) -> str:
    """
    Redact PII from content before storing in vector store.
    
    Args:
        content: Content potentially containing PII
        
    Returns:
        Content with PII redacted
    """
    sanitizer = LogSanitizer()
    return sanitizer.sanitize(content)

