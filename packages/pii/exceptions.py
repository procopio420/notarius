"""
PII-specific exceptions.
"""

from packages.core.exceptions import NotariusException


class PIIExtractionException(NotariusException):
    """Raised when PII extraction fails."""
    
    def __init__(self, message: str, text: str = None, extractor: str = None):
        super().__init__(
            message=message,
            error_code="PII_EXTRACTION_ERROR",
            details={
                "text": text,
                "extractor": extractor,
            }
        )


class PIIValidationException(NotariusException):
    """Raised when PII validation fails."""
    
    def __init__(self, message: str, pii_type: str = None, value: str = None):
        super().__init__(
            message=message,
            error_code="PII_VALIDATION_ERROR",
            details={
                "pii_type": pii_type,
                "value": value,
            }
        )


class MorphEngineException(NotariusException):
    """Raised when Portuguese morphology processing fails."""
    
    def __init__(self, message: str, template: str = None, placeholder: str = None):
        super().__init__(
            message=message,
            error_code="MORPH_ENGINE_ERROR",
            details={
                "template": template,
                "placeholder": placeholder,
            }
        )


class PlaceholderException(NotariusException):
    """Raised when placeholder operations fail."""
    
    def __init__(self, message: str, placeholder: str = None, operation: str = None):
        super().__init__(
            message=message,
            error_code="PLACEHOLDER_ERROR",
            details={
                "placeholder": placeholder,
                "operation": operation,
            }
        )
