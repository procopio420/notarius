"""
PII handling library for Privacy-First AI Notarius.

This package provides comprehensive PII extraction, validation, tokenization,
and morph engine functionality for Brazilian Portuguese legal documents.
"""

from .extractors import (
    MultiLayerPIIExtractor,
    RegexExtractor,
    SpacyNERExtractor,
    BERTNERExtractor,
    ValidationLayer,
    ScannerLayer,
)

from .validators import (
    CPFValidator,
    CNPJValidator,
    EmailValidator,
    PhoneValidator,
    BrazilianDocumentValidator,
)

from .morph_engine import (
    PortugueseMorphEngine,
    ContractionEngine,
    GenderAgreementEngine,
)

from .placeholders import (
    PlaceholderGenerator,
    PlaceholderResolver,
    PlaceholderValidator,
)

from .redaction import (
    PIIRedactionMiddleware,
    LogSanitizer,
    PIILeakDetector,
)

from .exceptions import (
    PIIExtractionException,
    PIIValidationException,
    MorphEngineException,
    PlaceholderException,
)

__all__ = [
    # Extractors
    "MultiLayerPIIExtractor",
    "RegexExtractor", 
    "SpacyNERExtractor",
    "BERTNERExtractor",
    "ValidationLayer",
    "ScannerLayer",
    
    # Validators
    "CPFValidator",
    "CNPJValidator",
    "EmailValidator",
    "PhoneValidator",
    "BrazilianDocumentValidator",
    
    # Morph Engine
    "PortugueseMorphEngine",
    "ContractionEngine",
    "GenderAgreementEngine",
    
    # Placeholders
    "PlaceholderGenerator",
    "PlaceholderResolver",
    "PlaceholderValidator",
    
    # Redaction
    "PIIRedactionMiddleware",
    "LogSanitizer",
    "PIILeakDetector",
    
    # Exceptions
    "PIIExtractionException",
    "PIIValidationException",
    "MorphEngineException",
    "PlaceholderException",
]
