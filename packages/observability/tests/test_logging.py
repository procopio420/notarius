"""
Tests for logging functionality.
"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from packages.observability.logging import (
    setup_logging, get_logger, 
    log_with_correlation, PIIFilter
)


class TestLoggingSetup:
    """Test cases for logging setup."""
    
    def test_setup_logging(self):
        """Test setting up logging configuration."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging()
            
            mock_basic_config.assert_called_once()
            call_args = mock_basic_config.call_args
            assert 'level' in call_args.kwargs
            assert 'format' in call_args.kwargs
    
    def test_setup_logging_with_level(self):
        """Test setting up logging with specific level."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(level=logging.DEBUG)
            
            mock_basic_config.assert_called_once()
            call_args = mock_basic_config.call_args
            assert call_args.kwargs['level'] == logging.DEBUG
    
    def test_get_logger(self):
        """Test getting a logger instance."""
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_get_logger_same_name(self):
        """Test getting logger with same name returns same instance."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")
        
        assert logger1 is logger2


class TestPIIFilter:
    """Test cases for PII filter."""
    
    @pytest.fixture
    def pii_filter(self):
        """Create a PII filter instance."""
        return PIIFilter()
    
    def test_pii_filter_creation(self):
        """Test creating a PII filter."""
        filter_instance = PIIFilter()
        
        assert isinstance(filter_instance, logging.Filter)
    
    def test_pii_filter_cpf_redaction(self, pii_filter):
        """Test PII filter redacts CPF."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User CPF 123.456.789-00 logged in",
            args=(),
            exc_info=None
        )
        
        result = pii_filter.filter(record)
        
        assert result is True
        assert "123.456.789-00" not in record.getMessage()
        assert "[PII_REDACTED]" in record.getMessage()
    
    def test_pii_filter_cnpj_redaction(self, pii_filter):
        """Test PII filter redacts CNPJ."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Company CNPJ 12.345.678/0001-90 registered",
            args=(),
            exc_info=None
        )
        
        result = pii_filter.filter(record)
        
        assert result is True
        assert "12.345.678/0001-90" not in record.getMessage()
        assert "[PII_REDACTED]" in record.getMessage()
    
    def test_pii_filter_email_redaction(self, pii_filter):
        """Test PII filter redacts email."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User email user@example.com sent notification",
            args=(),
            exc_info=None
        )
        
        result = pii_filter.filter(record)
        
        assert result is True
        assert "user@example.com" not in record.getMessage()
        assert "[PII_REDACTED]" in record.getMessage()
    
    def test_pii_filter_phone_redaction(self, pii_filter):
        """Test PII filter redacts phone."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User phone (21) 99999-9999 called",
            args=(),
            exc_info=None
        )
        
        result = pii_filter.filter(record)
        
        assert result is True
        assert "(21) 99999-9999" not in record.getMessage()
        assert "[PII_REDACTED]" in record.getMessage()
    
    def test_pii_filter_no_pii(self, pii_filter):
        """Test PII filter with no PII in message."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="System started successfully",
            args=(),
            exc_info=None
        )
        
        result = pii_filter.filter(record)
        
        assert result is True
        assert record.getMessage() == "System started successfully"
    
    def test_pii_filter_multiple_pii(self, pii_filter):
        """Test PII filter with multiple PII types."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User CPF 123.456.789-00, email user@example.com, phone (21) 99999-9999",
            args=(),
            exc_info=None
        )
        
        result = pii_filter.filter(record)
        
        assert result is True
        message = record.getMessage()
        assert "123.456.789-00" not in message
        assert "user@example.com" not in message
        assert "(21) 99999-9999" not in message
        assert message.count("[PII_REDACTED]") == 3


class TestLogWithCorrelation:
    """Test cases for logging with correlation ID."""
    
    def test_log_with_correlation(self):
        """Test logging with correlation ID."""
        with patch('packages.observability.correlation.get_correlation_id') as mock_get_id:
            mock_get_id.return_value = "test-correlation-id"
            
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                log_with_correlation("test_module", "Test message", level=logging.INFO)
                
                mock_logger.log.assert_called_once()
                call_args = mock_logger.log.call_args
                assert call_args[0][0] == logging.INFO
                assert "test-correlation-id" in call_args[0][1]
                assert "Test message" in call_args[0][1]
    
    def test_log_with_correlation_no_id(self):
        """Test logging with correlation ID when none is set."""
        with patch('packages.observability.correlation.get_correlation_id') as mock_get_id:
            mock_get_id.return_value = None
            
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                log_with_correlation("test_module", "Test message", level=logging.INFO)
                
                mock_logger.log.assert_called_once()
                call_args = mock_logger.log.call_args
                assert call_args[0][0] == logging.INFO
                assert "Test message" in call_args[0][1]
    
    def test_log_with_correlation_different_levels(self):
        """Test logging with correlation ID at different levels."""
        with patch('packages.observability.correlation.get_correlation_id') as mock_get_id:
            mock_get_id.return_value = "test-correlation-id"
            
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                
                # Test different log levels
                levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
                
                for level in levels:
                    log_with_correlation("test_module", f"Test message {level}", level=level)
                
                assert mock_logger.log.call_count == len(levels)
