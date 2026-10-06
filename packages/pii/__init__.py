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

# Optional modules - only import if they exist
try:
    from .placeholders import (
        PlaceholderGenerator,
        PlaceholderResolver,
        PlaceholderValidator,
    )
    _placeholders_available = True
except ImportError:
    _placeholders_available = False
    PlaceholderGenerator = None
    PlaceholderResolver = None
    PlaceholderValidator = None

try:
    from .redaction import (
        PIIRedactionMiddleware,
        LogSanitizer,
        PIILeakDetector,
    )
    _redaction_available = True
except ImportError:
    _redaction_available = False
    PIIRedactionMiddleware = None
    LogSanitizer = None
    PIILeakDetector = None

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
    
    # Exceptions
    "PIIExtractionException",
    "PIIValidationException",
    "MorphEngineException",
    "PlaceholderException",
]

# Conditionally add optional modules to __all__
if _placeholders_available:
    __all__.extend(["PlaceholderGenerator", "PlaceholderResolver", "PlaceholderValidator"])

if _redaction_available:
    __all__.extend(["PIIRedactionMiddleware", "LogSanitizer", "PIILeakDetector"])
