"""
Tests for PII extractors.
"""
import pytest
from unittest.mock import patch, MagicMock

from packages.pii.extractors import (
    CPFExtractor, CNPJExtractor, EmailExtractor, 
    PhoneExtractor, NameExtractor, AddressExtractor
)


class TestCPFExtractor:
    """Test cases for CPF extractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create a CPF extractor instance."""
        return CPFExtractor()
    
    def test_extract_valid_cpf(self, extractor):
        """Test extracting valid CPF."""
        text = "João Silva, CPF 123.456.789-00, residente no Rio de Janeiro"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "123.456.789-00"
    
    def test_extract_multiple_cpfs(self, extractor):
        """Test extracting multiple CPFs."""
        text = "CPF 123.456.789-00 e CPF 987.654.321-00"
        result = extractor.extract(text)
        
        assert len(result) == 2
        assert "123.456.789-00" in result
        assert "987.654.321-00" in result
    
    def test_extract_cpf_without_formatting(self, extractor):
        """Test extracting CPF without formatting."""
        text = "CPF 12345678900"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "12345678900"
    
    def test_extract_invalid_cpf(self, extractor):
        """Test extracting invalid CPF."""
        text = "CPF 123.456.789-99"  # Invalid check digits
        result = extractor.extract(text)
        
        assert len(result) == 0
    
    def test_extract_no_cpf(self, extractor):
        """Test extracting from text with no CPF."""
        text = "João Silva, residente no Rio de Janeiro"
        result = extractor.extract(text)
        
        assert len(result) == 0
    
    def test_extract_cpf_with_context(self, extractor):
        """Test extracting CPF with surrounding context."""
        text = "O documento apresenta o CPF 123.456.789-00 do interessado"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "123.456.789-00"
    
    def test_extract_cpf_special_characters(self, extractor):
        """Test extracting CPF with special characters."""
        text = "CPF: 123.456.789-00 (válido)"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "123.456.789-00"


class TestCNPJExtractor:
    """Test cases for CNPJ extractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create a CNPJ extractor instance."""
        return CNPJExtractor()
    
    def test_extract_valid_cnpj(self, extractor):
        """Test extracting valid CNPJ."""
        text = "Empresa XYZ, CNPJ 12.345.678/0001-90"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "12.345.678/0001-90"
    
    def test_extract_multiple_cnpjs(self, extractor):
        """Test extracting multiple CNPJs."""
        text = "CNPJ 12.345.678/0001-90 e CNPJ 98.765.432/0001-10"
        result = extractor.extract(text)
        
        assert len(result) == 2
        assert "12.345.678/0001-90" in result
        assert "98.765.432/0001-10" in result
    
    def test_extract_cnpj_without_formatting(self, extractor):
        """Test extracting CNPJ without formatting."""
        text = "CNPJ 12345678000190"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "12345678000190"
    
    def test_extract_invalid_cnpj(self, extractor):
        """Test extracting invalid CNPJ."""
        text = "CNPJ 12.345.678/0001-99"  # Invalid check digits
        result = extractor.extract(text)
        
        assert len(result) == 0
    
    def test_extract_no_cnpj(self, extractor):
        """Test extracting from text with no CNPJ."""
        text = "Empresa XYZ, localizada no Rio de Janeiro"
        result = extractor.extract(text)
        
        assert len(result) == 0


class TestEmailExtractor:
    """Test cases for Email extractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create an Email extractor instance."""
        return EmailExtractor()
    
    def test_extract_valid_email(self, extractor):
        """Test extracting valid email."""
        text = "Contato: joao.silva@email.com"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "joao.silva@email.com"
    
    def test_extract_multiple_emails(self, extractor):
        """Test extracting multiple emails."""
        text = "Emails: joao@email.com e maria@empresa.com.br"
        result = extractor.extract(text)
        
        assert len(result) == 2
        assert "joao@email.com" in result
        assert "maria@empresa.com.br" in result
    
    def test_extract_email_with_plus(self, extractor):
        """Test extracting email with plus sign."""
        text = "Email: joao.silva+test@email.com"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "joao.silva+test@email.com"
    
    def test_extract_email_with_subdomain(self, extractor):
        """Test extracting email with subdomain."""
        text = "Email: joao@mail.empresa.com.br"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "joao@mail.empresa.com.br"
    
    def test_extract_invalid_email(self, extractor):
        """Test extracting invalid email."""
        text = "Email: joao@email"  # Invalid domain
        result = extractor.extract(text)
        
        assert len(result) == 0
    
    def test_extract_no_email(self, extractor):
        """Test extracting from text with no email."""
        text = "João Silva, residente no Rio de Janeiro"
        result = extractor.extract(text)
        
        assert len(result) == 0


class TestPhoneExtractor:
    """Test cases for Phone extractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create a Phone extractor instance."""
        return PhoneExtractor()
    
    def test_extract_valid_phone(self, extractor):
        """Test extracting valid phone number."""
        text = "Telefone: (21) 99999-9999"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "(21) 99999-9999"
    
    def test_extract_multiple_phones(self, extractor):
        """Test extracting multiple phone numbers."""
        text = "Telefones: (21) 99999-9999 e (11) 88888-8888"
        result = extractor.extract(text)
        
        assert len(result) == 2
        assert "(21) 99999-9999" in result
        assert "(11) 88888-8888" in result
    
    def test_extract_phone_without_formatting(self, extractor):
        """Test extracting phone without formatting."""
        text = "Telefone: 21999999999"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "21999999999"
    
    def test_extract_phone_with_country_code(self, extractor):
        """Test extracting phone with country code."""
        text = "Telefone: +55 21 99999-9999"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "+55 21 99999-9999"
    
    def test_extract_landline_phone(self, extractor):
        """Test extracting landline phone."""
        text = "Telefone: (21) 3333-4444"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "(21) 3333-4444"
    
    def test_extract_invalid_phone(self, extractor):
        """Test extracting invalid phone number."""
        text = "Telefone: (21) 999"  # Too short
        result = extractor.extract(text)
        
        assert len(result) == 0
    
    def test_extract_no_phone(self, extractor):
        """Test extracting from text with no phone."""
        text = "João Silva, residente no Rio de Janeiro"
        result = extractor.extract(text)
        
        assert len(result) == 0


class TestNameExtractor:
    """Test cases for Name extractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create a Name extractor instance."""
        return NameExtractor()
    
    def test_extract_simple_name(self, extractor):
        """Test extracting simple name."""
        text = "João Silva"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "João Silva"
    
    def test_extract_full_name(self, extractor):
        """Test extracting full name."""
        text = "João Silva Santos"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "João Silva Santos"
    
    def test_extract_name_with_title(self, extractor):
        """Test extracting name with title."""
        text = "Dr. João Silva Santos"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "Dr. João Silva Santos"
    
    def test_extract_multiple_names(self, extractor):
        """Test extracting multiple names."""
        text = "João Silva e Maria Santos"
        result = extractor.extract(text)
        
        assert len(result) == 2
        assert "João Silva" in result
        assert "Maria Santos" in result
    
    def test_extract_name_with_context(self, extractor):
        """Test extracting name with surrounding context."""
        text = "O interessado João Silva Santos compareceu ao cartório"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "João Silva Santos"
    
    def test_extract_name_with_unicode(self, extractor):
        """Test extracting name with unicode characters."""
        text = "José da Silva (com acentos: ção, ñ, ü)"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "José da Silva"
    
    def test_extract_no_name(self, extractor):
        """Test extracting from text with no name."""
        text = "Documento de procuração para compra e venda"
        result = extractor.extract(text)
        
        assert len(result) == 0


class TestAddressExtractor:
    """Test cases for Address extractor."""
    
    @pytest.fixture
    def extractor(self):
        """Create an Address extractor instance."""
        return AddressExtractor()
    
    def test_extract_simple_address(self, extractor):
        """Test extracting simple address."""
        text = "Rua das Flores, 123"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "Rua das Flores, 123"
    
    def test_extract_full_address(self, extractor):
        """Test extracting full address."""
        text = "Rua das Flores, 123, Centro, Rio de Janeiro - RJ"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "Rua das Flores, 123, Centro, Rio de Janeiro - RJ"
    
    def test_extract_address_with_cep(self, extractor):
        """Test extracting address with CEP."""
        text = "Rua das Flores, 123, Centro, Rio de Janeiro - RJ, CEP 20000-000"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "Rua das Flores, 123, Centro, Rio de Janeiro - RJ, CEP 20000-000"
    
    def test_extract_multiple_addresses(self, extractor):
        """Test extracting multiple addresses."""
        text = "Endereço: Rua das Flores, 123 e Avenida Brasil, 456"
        result = extractor.extract(text)
        
        assert len(result) == 2
        assert "Rua das Flores, 123" in result
        assert "Avenida Brasil, 456" in result
    
    def test_extract_address_with_context(self, extractor):
        """Test extracting address with surrounding context."""
        text = "O interessado reside na Rua das Flores, 123, Centro"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "Rua das Flores, 123, Centro"
    
    def test_extract_address_with_unicode(self, extractor):
        """Test extracting address with unicode characters."""
        text = "Rua da Consolação, 123, São Paulo - SP"
        result = extractor.extract(text)
        
        assert len(result) == 1
        assert result[0] == "Rua da Consolação, 123, São Paulo - SP"
    
    def test_extract_no_address(self, extractor):
        """Test extracting from text with no address."""
        text = "Documento de procuração para compra e venda"
        result = extractor.extract(text)
        
        assert len(result) == 0


class TestPIIExtractorIntegration:
    """Test cases for PII extractor integration."""
    
    def test_extract_all_pii_types(self):
        """Test extracting all PII types from a single text."""
        text = """
        João Silva Santos, CPF 123.456.789-00, CNPJ 12.345.678/0001-90,
        residente na Rua das Flores, 123, Centro, Rio de Janeiro - RJ,
        telefone (21) 99999-9999, email joao.silva@email.com
        """
        
        extractors = [
            CPFExtractor(),
            CNPJExtractor(),
            EmailExtractor(),
            PhoneExtractor(),
            NameExtractor(),
            AddressExtractor()
        ]
        
        results = {}
        for extractor in extractors:
            pii_type = extractor.__class__.__name__.replace('Extractor', '').lower()
            results[pii_type] = extractor.extract(text)
        
        assert len(results['cpf']) == 1
        assert results['cpf'][0] == "123.456.789-00"
        
        assert len(results['cnpj']) == 1
        assert results['cnpj'][0] == "12.345.678/0001-90"
        
        assert len(results['email']) == 1
        assert results['email'][0] == "joao.silva@email.com"
        
        assert len(results['phone']) == 1
        assert results['phone'][0] == "(21) 99999-9999"
        
        assert len(results['name']) == 1
        assert results['name'][0] == "João Silva Santos"
        
        assert len(results['address']) == 1
        assert "Rua das Flores, 123" in results['address'][0]
    
    def test_extract_pii_with_special_characters(self):
        """Test extracting PII with special characters."""
        text = "João Silva (Dr.), CPF: 123.456.789-00, email: joao.silva+test@email.com"
        
        extractors = [
            CPFExtractor(),
            EmailExtractor(),
            NameExtractor()
        ]
        
        results = {}
        for extractor in extractors:
            pii_type = extractor.__class__.__name__.replace('Extractor', '').lower()
            results[pii_type] = extractor.extract(text)
        
        assert len(results['cpf']) == 1
        assert results['cpf'][0] == "123.456.789-00"
        
        assert len(results['email']) == 1
        assert results['email'][0] == "joao.silva+test@email.com"
        
        assert len(results['name']) == 1
        assert "João Silva" in results['name'][0]
    
    def test_extract_pii_with_unicode(self):
        """Test extracting PII with unicode characters."""
        text = "José da Silva (com acentos: ção, ñ, ü), CPF 123.456.789-00"
        
        extractors = [
            CPFExtractor(),
            NameExtractor()
        ]
        
        results = {}
        for extractor in extractors:
            pii_type = extractor.__class__.__name__.replace('Extractor', '').lower()
            results[pii_type] = extractor.extract(text)
        
        assert len(results['cpf']) == 1
        assert results['cpf'][0] == "123.456.789-00"
        
        assert len(results['name']) == 1
        assert "José da Silva" in results['name'][0]
    
    def test_extract_pii_empty_text(self):
        """Test extracting PII from empty text."""
        text = ""
        
        extractors = [
            CPFExtractor(),
            CNPJExtractor(),
            EmailExtractor(),
            PhoneExtractor(),
            NameExtractor(),
            AddressExtractor()
        ]
        
        for extractor in extractors:
            result = extractor.extract(text)
            assert len(result) == 0
    
    def test_extract_pii_none_text(self):
        """Test extracting PII from None text."""
        text = None
        
        extractors = [
            CPFExtractor(),
            CNPJExtractor(),
            EmailExtractor(),
            PhoneExtractor(),
            NameExtractor(),
            AddressExtractor()
        ]
        
        for extractor in extractors:
            with pytest.raises((TypeError, AttributeError)):
                extractor.extract(text)
    
    def test_extract_pii_large_text(self):
        """Test extracting PII from large text."""
        # Create a large text with PII scattered throughout
        text = "João Silva, CPF 123.456.789-00, " * 1000
        
        extractors = [
            CPFExtractor(),
            NameExtractor()
        ]
        
        for extractor in extractors:
            result = extractor.extract(text)
            # Should handle large text without issues
            assert isinstance(result, list)
