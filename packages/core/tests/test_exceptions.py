"""
Tests for core exceptions.
"""
import pytest
from packages.core.exceptions import (
    NotariusException, ValidationError, PIIError, 
    DocumentError, ProcessError, ServiceError
)


class TestNotariusException:
    """Test cases for NotariusException."""
    
    def test_notarius_exception_creation(self):
        """Test creating a NotariusException."""
        message = "Test error message"
        exception = NotariusException(message)
        
        assert str(exception) == message
        assert exception.message == message
    
    def test_notarius_exception_with_code(self):
        """Test creating a NotariusException with error code."""
        message = "Test error message"
        code = "TEST_ERROR"
        exception = NotariusException(message, code=code)
        
        assert str(exception) == message
        assert exception.message == message
        assert exception.code == code
    
    def test_notarius_exception_inheritance(self):
        """Test that NotariusException inherits from Exception."""
        exception = NotariusException("Test")
        
        assert isinstance(exception, Exception)


class TestValidationError:
    """Test cases for ValidationError."""
    
    def test_validation_error_creation(self):
        """Test creating a ValidationError."""
        message = "Validation failed"
        exception = ValidationError(message)
        
        assert str(exception) == message
        assert exception.message == message
    
    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from NotariusException."""
        exception = ValidationError("Test")
        
        assert isinstance(exception, NotariusException)
    
    def test_validation_error_with_field(self):
        """Test creating a ValidationError with field."""
        message = "Field is required"
        field = "name"
        exception = ValidationError(message, field=field)
        
        assert exception.message == message
        assert exception.field == field


class TestPIIError:
    """Test cases for PIIError."""
    
    def test_pii_error_creation(self):
        """Test creating a PIIError."""
        message = "PII processing failed"
        exception = PIIError(message)
        
        assert str(exception) == message
        assert exception.message == message
    
    def test_pii_error_inheritance(self):
        """Test that PIIError inherits from NotariusException."""
        exception = PIIError("Test")
        
        assert isinstance(exception, NotariusException)
    
    def test_pii_error_with_type(self):
        """Test creating a PIIError with PII type."""
        message = "CPF validation failed"
        pii_type = "cpf"
        exception = PIIError(message, pii_type=pii_type)
        
        assert exception.message == message
        assert exception.pii_type == pii_type


class TestDocumentError:
    """Test cases for DocumentError."""
    
    def test_document_error_creation(self):
        """Test creating a DocumentError."""
        message = "Document processing failed"
        exception = DocumentError(message)
        
        assert str(exception) == message
        assert exception.message == message
    
    def test_document_error_inheritance(self):
        """Test that DocumentError inherits from NotariusException."""
        exception = DocumentError("Test")
        
        assert isinstance(exception, NotariusException)
    
    def test_document_error_with_document_id(self):
        """Test creating a DocumentError with document ID."""
        message = "Document not found"
        document_id = "doc_123"
        exception = DocumentError(message, document_id=document_id)
        
        assert exception.message == message
        assert exception.document_id == document_id


class TestProcessError:
    """Test cases for ProcessError."""
    
    def test_process_error_creation(self):
        """Test creating a ProcessError."""
        message = "Process failed"
        exception = ProcessError(message)
        
        assert str(exception) == message
        assert exception.message == message
    
    def test_process_error_inheritance(self):
        """Test that ProcessError inherits from NotariusException."""
        exception = ProcessError("Test")
        
        assert isinstance(exception, NotariusException)
    
    def test_process_error_with_process_id(self):
        """Test creating a ProcessError with process ID."""
        message = "Process not found"
        process_id = "proc_123"
        exception = ProcessError(message, process_id=process_id)
        
        assert exception.message == message
        assert exception.process_id == process_id


class TestServiceError:
    """Test cases for ServiceError."""
    
    def test_service_error_creation(self):
        """Test creating a ServiceError."""
        message = "Service unavailable"
        exception = ServiceError(message)
        
        assert str(exception) == message
        assert exception.message == message
    
    def test_service_error_inheritance(self):
        """Test that ServiceError inherits from NotariusException."""
        exception = ServiceError("Test")
        
        assert isinstance(exception, NotariusException)
    
    def test_service_error_with_service_name(self):
        """Test creating a ServiceError with service name."""
        message = "Service error"
        service_name = "lexnode"
        exception = ServiceError(message, service_name=service_name)
        
        assert exception.message == message
        assert exception.service_name == service_name
