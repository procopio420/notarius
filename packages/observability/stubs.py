"""
Stub implementations for observability when full stack isn't available.
"""

import logging

logger = logging.getLogger(__name__)


def setup_tracing_stub(service_name: str, service_version: str = "1.0.0"):
    """Stub for tracing setup."""
    logger.info(f"Tracing stub initialized for {service_name}")


def setup_logging_stub(service_name: str, log_level: str = "INFO"):
    """Stub for logging setup."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger.info(f"Logging stub initialized for {service_name}")


def setup_metrics_stub(service_name: str):
    """Stub for metrics setup."""
    logger.info(f"Metrics stub initialized for {service_name}")


def setup_correlation_stub():
    """Stub for correlation setup."""
    logger.info("Correlation stub initialized")

