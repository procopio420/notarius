"""
Tests for PII validators.
"""
import pytest
from packages.pii.validators import CPFValidator, CNPJValidator, EmailValidator


class TestCPFValidator:
    """Test cases for CPF validator."""
    
    @pytest.fixture
    def validator(self):
        """Create a CPF validator instance."""
        return CPFValidator()
    
    def test_validate_valid_cpf(self, validator):
        """Test validating valid CPF."""
        valid_cpfs = [
            "123.456.789-00",
            "12345678900",
            "111.444.777-35",
            "11144477735"
        ]
        
        for cpf in valid_cpfs:
            assert validator.validate(cpf) is True
    
    def test_validate_invalid_cpf(self, validator):
        """Test validating invalid CPF."""
        invalid_cpfs = [
            "123.456.789-99",  # Wrong check digits
            "12345678999",
            "111.111.111-11",  # All same digits
            "11111111111",
            "123.456.789-0",   # Too short
            "123.456.789-000", # Too long
            "abc.def.ghi-jk",  # Non-numeric
            ""
        ]
        
        for cpf in invalid_cpfs:
            assert validator.validate(cpf) is False
    
    def test_validate_cpf_none(self, validator):
        """Test validating None CPF."""
        assert validator.validate(None) is False
    
    def test_validate_cpf_empty_string(self, validator):
        """Test validating empty string CPF."""
        assert validator.validate("") is False


class TestCNPJValidator:
    """Test cases for CNPJ validator."""
    
    @pytest.fixture
    def validator(self):
        """Create a CNPJ validator instance."""
        return CNPJValidator()
    
    def test_validate_valid_cnpj(self, validator):
        """Test validating valid CNPJ."""
        valid_cnpjs = [
            "12.345.678/0001-90",
            "12345678000190",
            "11.222.333/0001-81",
            "11222333000181"
        ]
        
        for cnpj in valid_cnpjs:
            assert validator.validate(cnpj) is True
    
    def test_validate_invalid_cnpj(self, validator):
        """Test validating invalid CNPJ."""
        invalid_cnpjs = [
            "12.345.678/0001-99",  # Wrong check digits
            "12345678000199",
            "11.111.111/1111-11",  # All same digits
            "11111111111111",
            "12.345.678/0001-9",   # Too short
            "12.345.678/0001-900", # Too long
            "ab.cde.fgh/ijkl-mn",  # Non-numeric
            ""
        ]
        
        for cnpj in invalid_cnpjs:
            assert validator.validate(cnpj) is False
    
    def test_validate_cnpj_none(self, validator):
        """Test validating None CNPJ."""
        assert validator.validate(None) is False
    
    def test_validate_cnpj_empty_string(self, validator):
        """Test validating empty string CNPJ."""
        assert validator.validate("") is False


class TestEmailValidator:
    """Test cases for Email validator."""
    
    @pytest.fixture
    def validator(self):
        """Create an Email validator instance."""
        return EmailValidator()
    
    def test_validate_valid_email(self, validator):
        """Test validating valid email addresses."""
        valid_emails = [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.com",
            "user@sub.example.com",
            "user@example.com.br",
            "user123@example123.com"
        ]
        
        for email in valid_emails:
            assert validator.validate(email) is True
    
    def test_validate_invalid_email(self, validator):
        """Test validating invalid email addresses."""
        invalid_emails = [
            "user@",  # No domain
            "@example.com",  # No user
            "user@",  # Incomplete
            "user.example.com",  # No @
            "user@.com",  # Empty domain
            "user@example",  # No TLD
            "user@example.",  # Incomplete TLD
            "user name@example.com",  # Space in user
            "user@example .com",  # Space in domain
            ""
        ]
        
        for email in invalid_emails:
            assert validator.validate(email) is False
    
    def test_validate_email_none(self, validator):
        """Test validating None email."""
        assert validator.validate(None) is False
    
    def test_validate_email_empty_string(self, validator):
        """Test validating empty string email."""
        assert validator.validate("") is False
