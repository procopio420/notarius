"""
Core domain models and shared business logic for Privacy-First AI Notarius.

This package contains Pydantic models that are shared between Django (converted to ORM)
and FastAPI services (used directly). It ensures type safety and consistency across
all services in the monorepo.
"""

from .models import (
    Act,
    Party,
    Draft,
    Clause,
    Citation,
    AuditEvent,
    Intent,
    PIIEntity,
    TokenResult,
    CacheKey,
    TRELLISCluster,
)

from .enums import (
    ActType,
    PartyRole,
    DocumentStatus,
    Jurisdiction,
    PIIEntityType,
    AuditAction,
)

from .exceptions import (
    NotariusException,
    PIILeakException,
    InsufficientGroundingException,
    CacheMissException,
    TRELLISException,
)

__all__ = [
    # Models
    "Act",
    "Party", 
    "Draft",
    "Clause",
    "Citation",
    "AuditEvent",
    "Intent",
    "PIIEntity",
    "TokenResult",
    "CacheKey",
    "TRELLISCluster",
    
    # Enums
    "ActType",
    "PartyRole",
    "DocumentStatus",
    "Jurisdiction",
    "PIIEntityType",
    "AuditAction",
    
    # Exceptions
    "NotariusException",
    "PIILeakException",
    "InsufficientGroundingException",
    "CacheMissException",
    "TRELLISException",
]
