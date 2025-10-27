"""
Structured logging setup for all services
"""

import json
import logging
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import uuid


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "version": self.service_version,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_entry["correlation_id"] = record.correlation_id
        
        # Add user ID if available
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        # Add tenant ID if available
        if hasattr(record, 'tenant_id'):
            log_entry["tenant_id"] = record.tenant_id
        
        # Add custom fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if available
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class CorrelationIDFilter(logging.Filter):
    """Filter to add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        # Get correlation ID from context or generate new one
        correlation_id = getattr(record, 'correlation_id', None)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
            record.correlation_id = correlation_id
        
        return True


class PIIRedactionFilter(logging.Filter):
    """Filter to redact PII from log records."""
    
    def __init__(self):
        super().__init__()
        # PII patterns to redact
        self.pii_patterns = [
            (r'\b\d{3}\.\d{3}\.\d{3}-\d{2}\b', '[CPF_REDACTED]'),  # CPF
            (r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', '[CNPJ_REDACTED]'),  # CNPJ
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),  # Email
            (r'\b\(\d{2}\)\s?\d{4,5}-?\d{4}\b', '[PHONE_REDACTED]'),  # Phone
        ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Redact PII from log record message."""
        import re
        
        message = record.getMessage()
        redacted_message = message
        
        for pattern, replacement in self.pii_patterns:
            redacted_message = re.sub(pattern, replacement, redacted_message)
        
        if redacted_message != message:
            # PII was detected and redacted
            record.msg = redacted_message
            record.args = ()
            
            # Add PII detection flag
            if not hasattr(record, 'extra_fields'):
                record.extra_fields = {}
            record.extra_fields['pii_detected'] = True
        
        return True


class LoggingSetup:
    """Logging configuration for services."""
    
    def __init__(self, service_name: str, service_version: str = "1.0.0", log_level: str = "INFO"):
        self.service_name = service_name
        self.service_version = service_version
        self.log_level = log_level
        self._setup_logging()
    
    def _setup_logging(self):
        """Initialize structured logging."""
        try:
            # Get root logger
            logger = logging.getLogger()
            logger.setLevel(getattr(logging, self.log_level.upper()))
            
            # Remove existing handlers
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
            
            # Create console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.log_level.upper()))
            
            # Set up formatter
            formatter = StructuredFormatter(self.service_name, self.service_version)
            console_handler.setFormatter(formatter)
            
            # Add filters
            console_handler.addFilter(CorrelationIDFilter())
            console_handler.addFilter(PIIRedactionFilter())
            
            # Add handler to logger
            logger.addHandler(console_handler)
            
            # Set up specific loggers
            self._setup_service_loggers()
            
            logging.info(f"Structured logging initialized for {self.service_name}")
            
        except Exception as e:
            print(f"Failed to initialize structured logging: {e}")
    
    def _setup_service_loggers(self):
        """Set up specific service loggers."""
        # Set log levels for specific modules
        logging.getLogger("uvicorn").setLevel(logging.INFO)
        logging.getLogger("fastapi").setLevel(logging.INFO)
        logging.getLogger("django").setLevel(logging.INFO)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("boto3").setLevel(logging.WARNING)
        logging.getLogger("botocore").setLevel(logging.WARNING)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the given name."""
        return logging.getLogger(name)


# Global logging setups
_logging_setups: Dict[str, LoggingSetup] = {}


def get_logging_setup(service_name: str) -> LoggingSetup:
    """Get or create a logging setup for a service."""
    if service_name not in _logging_setups:
        _logging_setups[service_name] = LoggingSetup(service_name)
    return _logging_setups[service_name]


def get_logger(service_name: str, name: str = None) -> logging.Logger:
    """Get a logger for a service."""
    if name is None:
        name = service_name
    return get_logging_setup(service_name).get_logger(name)


def log_with_context(
    logger: logging.Logger,
    level: int,
    message: str,
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """Log a message with additional context."""
    extra = {}
    
    if correlation_id:
        extra['correlation_id'] = correlation_id
    if user_id:
        extra['user_id'] = user_id
    if tenant_id:
        extra['tenant_id'] = tenant_id
    if extra_fields:
        extra['extra_fields'] = extra_fields
    
    # Add any additional kwargs
    extra.update(kwargs)
    
    logger.log(level, message, extra=extra)


def log_info(
    logger: logging.Logger,
    message: str,
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """Log an info message with context."""
    log_with_context(
        logger, logging.INFO, message, correlation_id, user_id, tenant_id, extra_fields, **kwargs
    )


def log_warning(
    logger: logging.Logger,
    message: str,
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """Log a warning message with context."""
    log_with_context(
        logger, logging.WARNING, message, correlation_id, user_id, tenant_id, extra_fields, **kwargs
    )


def log_error(
    logger: logging.Logger,
    message: str,
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """Log an error message with context."""
    log_with_context(
        logger, logging.ERROR, message, correlation_id, user_id, tenant_id, extra_fields, **kwargs
    )


def log_exception(
    logger: logging.Logger,
    message: str,
    exc_info: bool = True,
    correlation_id: Optional[str] = None,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    extra_fields: Optional[Dict[str, Any]] = None,
    **kwargs
):
    """Log an exception with context."""
    extra = {}
    
    if correlation_id:
        extra['correlation_id'] = correlation_id
    if user_id:
        extra['user_id'] = user_id
    if tenant_id:
        extra['tenant_id'] = tenant_id
    if extra_fields:
        extra['extra_fields'] = extra_fields
    
    # Add any additional kwargs
    extra.update(kwargs)
    
    logger.exception(message, exc_info=exc_info, extra=extra)


class LogContext:
    """Context manager for adding context to logs."""
    
    def __init__(self, **kwargs):
        self.context = kwargs
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def setup_logging(service_name: str, log_level: str = "INFO"):
    """Setup logging for a service."""
    get_logging_setup(service_name)
    logging.info(f"Logging setup complete for {service_name}")