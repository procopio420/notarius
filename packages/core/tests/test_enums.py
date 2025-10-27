"""
Tests for core enums.
"""
import pytest
from packages.core.enums import DocumentType, ProcessStatus, PIIType


class TestDocumentType:
    """Test cases for DocumentType enum."""
    
    def test_document_type_values(self):
        """Test DocumentType enum values."""
        assert DocumentType.PROCURACAO.value == "procuracao"
        assert DocumentType.CERTIDAO.value == "certidao"
        assert DocumentType.TESTAMENTO.value == "testamento"
        assert DocumentType.ESCRITURA.value == "escritura"
        assert DocumentType.CONTRATO.value == "contrato"
    
    def test_document_type_choices(self):
        """Test DocumentType choices."""
        choices = DocumentType.choices()
        
        assert len(choices) == 5
        assert ("procuracao", "Procuração") in choices
        assert ("certidao", "Certidão") in choices
        assert ("testamento", "Testamento") in choices
        assert ("escritura", "Escritura") in choices
        assert ("contrato", "Contrato") in choices
    
    def test_document_type_from_value(self):
        """Test getting DocumentType from value."""
        assert DocumentType.from_value("procuracao") == DocumentType.PROCURACAO
        assert DocumentType.from_value("certidao") == DocumentType.CERTIDAO
        assert DocumentType.from_value("testamento") == DocumentType.TESTAMENTO
        assert DocumentType.from_value("escritura") == DocumentType.ESCRITURA
        assert DocumentType.from_value("contrato") == DocumentType.CONTRATO
    
    def test_document_type_invalid_value(self):
        """Test getting DocumentType from invalid value."""
        with pytest.raises(ValueError):
            DocumentType.from_value("invalid")


class TestProcessStatus:
    """Test cases for ProcessStatus enum."""
    
    def test_process_status_values(self):
        """Test ProcessStatus enum values."""
        assert ProcessStatus.DRAFT.value == "draft"
        assert ProcessStatus.REVIEW.value == "review"
        assert ProcessStatus.APPROVED.value == "approved"
        assert ProcessStatus.REJECTED.value == "rejected"
        assert ProcessStatus.FINALIZED.value == "finalized"
    
    def test_process_status_choices(self):
        """Test ProcessStatus choices."""
        choices = ProcessStatus.choices()
        
        assert len(choices) == 5
        assert ("draft", "Rascunho") in choices
        assert ("review", "Em Revisão") in choices
        assert ("approved", "Aprovado") in choices
        assert ("rejected", "Rejeitado") in choices
        assert ("finalized", "Finalizado") in choices
    
    def test_process_status_from_value(self):
        """Test getting ProcessStatus from value."""
        assert ProcessStatus.from_value("draft") == ProcessStatus.DRAFT
        assert ProcessStatus.from_value("review") == ProcessStatus.REVIEW
        assert ProcessStatus.from_value("approved") == ProcessStatus.APPROVED
        assert ProcessStatus.from_value("rejected") == ProcessStatus.REJECTED
        assert ProcessStatus.from_value("finalized") == ProcessStatus.FINALIZED
    
    def test_process_status_invalid_value(self):
        """Test getting ProcessStatus from invalid value."""
        with pytest.raises(ValueError):
            ProcessStatus.from_value("invalid")


class TestPIIType:
    """Test cases for PIIType enum."""
    
    def test_pii_type_values(self):
        """Test PIIType enum values."""
        assert PIIType.CPF.value == "cpf"
        assert PIIType.CNPJ.value == "cnpj"
        assert PIIType.EMAIL.value == "email"
        assert PIIType.PHONE.value == "phone"
        assert PIIType.NAME.value == "name"
        assert PIIType.ADDRESS.value == "address"
    
    def test_pii_type_choices(self):
        """Test PIIType choices."""
        choices = PIIType.choices()
        
        assert len(choices) == 6
        assert ("cpf", "CPF") in choices
        assert ("cnpj", "CNPJ") in choices
        assert ("email", "Email") in choices
        assert ("phone", "Telefone") in choices
        assert ("name", "Nome") in choices
        assert ("address", "Endereço") in choices
    
    def test_pii_type_from_value(self):
        """Test getting PIIType from value."""
        assert PIIType.from_value("cpf") == PIIType.CPF
        assert PIIType.from_value("cnpj") == PIIType.CNPJ
        assert PIIType.from_value("email") == PIIType.EMAIL
        assert PIIType.from_value("phone") == PIIType.PHONE
        assert PIIType.from_value("name") == PIIType.NAME
        assert PIIType.from_value("address") == PIIType.ADDRESS
    
    def test_pii_type_invalid_value(self):
        """Test getting PIIType from invalid value."""
        with pytest.raises(ValueError):
            PIIType.from_value("invalid")
