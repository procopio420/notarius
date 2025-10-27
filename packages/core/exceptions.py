"""
Custom exceptions for the Notarius system.
"""


class NotariusException(Exception):
    """Base exception for all Notarius-related errors."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class PIILeakException(NotariusException):
    """Raised when PII is detected in a context where it shouldn't be."""
    
    def __init__(self, message: str, detected_pii: list = None, context: str = None):
        super().__init__(
            message=message,
            error_code="PII_LEAK",
            details={
                "detected_pii": detected_pii or [],
                "context": context,
            }
        )


class InsufficientGroundingException(NotariusException):
    """Raised when LexNode cannot provide sufficient legal grounding."""
    
    def __init__(self, message: str, query: str = None, confidence: float = None):
        super().__init__(
            message=message,
            error_code="INSUFFICIENT_GROUNDING",
            details={
                "query": query,
                "confidence": confidence,
            }
        )


class CacheMissException(NotariusException):
    """Raised when expected cache entry is not found."""
    
    def __init__(self, message: str, cache_key: str = None, strategy: str = None):
        super().__init__(
            message=message,
            error_code="CACHE_MISS",
            details={
                "cache_key": cache_key,
                "strategy": strategy,
            }
        )


class TRELLISException(NotariusException):
    """Raised when TRELLIS clustering or parsing fails."""
    
    def __init__(self, message: str, cluster_id: str = None, command: str = None):
        super().__init__(
            message=message,
            error_code="TRELLIS_ERROR",
            details={
                "cluster_id": cluster_id,
                "command": command,
            }
        )


class VaultException(NotariusException):
    """Raised when PII Vault operations fail."""
    
    def __init__(self, message: str, operation: str = None, token_handle: str = None):
        super().__init__(
            message=message,
            error_code="VAULT_ERROR",
            details={
                "operation": operation,
                "token_handle": token_handle,
            }
        )


class LexNodeException(NotariusException):
    """Raised when LexNode RAG operations fail."""
    
    def __init__(self, message: str, operation: str = None, query: str = None):
        super().__init__(
            message=message,
            error_code="LEXNODE_ERROR",
            details={
                "operation": operation,
                "query": query,
            }
        )


class IntentEngineException(NotariusException):
    """Raised when Intent Engine operations fail."""
    
    def __init__(self, message: str, operation: str = None, command: str = None):
        super().__init__(
            message=message,
            error_code="INTENT_ENGINE_ERROR",
            details={
                "operation": operation,
                "command": command,
            }
        )


class ValidationException(NotariusException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: str = None, value: str = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={
                "field": field,
                "value": value,
            }
        )


class AuthenticationException(NotariusException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, user_id: str = None):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            details={
                "user_id": user_id,
            }
        )


class AuthorizationException(NotariusException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str, user_id: str = None, resource: str = None):
        super().__init__(
            message=message,
            error_code="AUTHZ_ERROR",
            details={
                "user_id": user_id,
                "resource": resource,
            }
        )
