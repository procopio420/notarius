"""
Unit tests for PII extraction functionality
"""

import pytest
from apps.pii_vault.app.services.extraction import PIIExtractor


class TestPIIExtractor:
    """Test PII extraction functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = PIIExtractor()
    
    def test_extract_cpf(self):
        """Test CPF extraction."""
        text = "João Silva, CPF 123.456.789-00, mora em São Paulo."
        entities = self.extractor.extract(text)
        
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        assert len(cpf_entities) == 1
        assert cpf_entities[0]["value"] == "123.456.789-00"
        assert cpf_entities[0]["start"] == 15
        assert cpf_entities[0]["end"] == 28
    
    def test_extract_cnpj(self):
        """Test CNPJ extraction."""
        text = "Empresa ABC Ltda, CNPJ 12.345.678/0001-90, situada em São Paulo."
        entities = self.extractor.extract(text)
        
        cnpj_entities = [e for e in entities if e["type"] == "cnpj"]
        assert len(cnpj_entities) == 1
        assert cnpj_entities[0]["value"] == "12.345.678/0001-90"
        assert cnpj_entities[0]["start"] == 20
        assert cnpj_entities[0]["end"] == 37
    
    def test_extract_email(self):
        """Test email extraction."""
        text = "Contato: joao.silva@email.com ou maria@empresa.com.br"
        entities = self.extractor.extract(text)
        
        email_entities = [e for e in entities if e["type"] == "email"]
        assert len(email_entities) == 2
        assert email_entities[0]["value"] == "joao.silva@email.com"
        assert email_entities[1]["value"] == "maria@empresa.com.br"
    
    def test_extract_phone(self):
        """Test phone number extraction."""
        text = "Telefone: (11) 99999-9999 ou 11 3333-4444"
        entities = self.extractor.extract(text)
        
        phone_entities = [e for e in entities if e["type"] == "phone"]
        assert len(phone_entities) == 2
        assert phone_entities[0]["value"] == "(11) 99999-9999"
        assert phone_entities[1]["value"] == "11 3333-4444"
    
    def test_extract_address(self):
        """Test address extraction."""
        text = "Endereço: Rua das Flores, 123, Bairro Centro, São Paulo - SP, CEP 01234-567"
        entities = self.extractor.extract(text)
        
        address_entities = [e for e in entities if e["type"] == "address"]
        assert len(address_entities) == 1
        assert "Rua das Flores" in address_entities[0]["value"]
        assert "123" in address_entities[0]["value"]
        assert "São Paulo" in address_entities[0]["value"]
    
    def test_extract_cep(self):
        """Test CEP extraction."""
        text = "CEP 01234-567 ou 12345-678"
        entities = self.extractor.extract(text)
        
        cep_entities = [e for e in entities if e["type"] == "cep"]
        assert len(cep_entities) == 2
        assert cep_entities[0]["value"] == "01234-567"
        assert cep_entities[1]["value"] == "12345-678"
    
    def test_extract_multiple_entities(self):
        """Test extraction of multiple entity types."""
        text = """
        João Silva, CPF 123.456.789-00,
        email: joao@email.com,
        telefone: (11) 99999-9999,
        endereço: Rua das Flores, 123, São Paulo - SP, CEP 01234-567
        """
        
        entities = self.extractor.extract(text)
        
        # Check that all entity types are found
        entity_types = {e["type"] for e in entities}
        expected_types = {"cpf", "email", "phone", "address", "cep"}
        assert entity_types.issuperset(expected_types)
        
        # Check specific values
        cpf_entity = next(e for e in entities if e["type"] == "cpf")
        assert cpf_entity["value"] == "123.456.789-00"
        
        email_entity = next(e for e in entities if e["type"] == "email")
        assert email_entity["value"] == "joao@email.com"
    
    def test_extract_no_entities(self):
        """Test extraction when no entities are present."""
        text = "Este é um texto sem informações pessoais."
        entities = self.extractor.extract(text)
        
        assert len(entities) == 0
    
    def test_extract_case_insensitive(self):
        """Test that extraction is case insensitive."""
        text = "CPF: 123.456.789-00 e cpf: 987.654.321-00"
        entities = self.extractor.extract(text)
        
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        assert len(cpf_entities) == 2
        assert cpf_entities[0]["value"] == "123.456.789-00"
        assert cpf_entities[1]["value"] == "987.654.321-00"
    
    def test_extract_with_context(self):
        """Test extraction with context preservation."""
        text = "João Silva, CPF 123.456.789-00, mora em São Paulo."
        entities = self.extractor.extract(text)
        
        cpf_entity = next(e for e in entities if e["type"] == "cpf")
        assert "context" in cpf_entity
        assert "João Silva" in cpf_entity["context"]
    
    def test_extract_confidence_scores(self):
        """Test that entities have confidence scores."""
        text = "João Silva, CPF 123.456.789-00"
        entities = self.extractor.extract(text)
        
        cpf_entity = next(e for e in entities if e["type"] == "cpf")
        assert "confidence" in cpf_entity
        assert 0.0 <= cpf_entity["confidence"] <= 1.0
    
    def test_extract_invalid_cpf(self):
        """Test that invalid CPF formats are not extracted."""
        text = "CPF: 123.456.789-99"  # Invalid CPF
        entities = self.extractor.extract(text)
        
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        assert len(cpf_entities) == 0  # Should not extract invalid CPF
    
    def test_extract_partial_matches(self):
        """Test extraction of partial matches."""
        text = "CPF: 123.456.789-00 e CNPJ: 12.345.678/0001-90"
        entities = self.extractor.extract(text)
        
        # Should extract both CPF and CNPJ
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        cnpj_entities = [e for e in entities if e["type"] == "cnpj"]
        
        assert len(cpf_entities) == 1
        assert len(cnpj_entities) == 1
    
    def test_extract_overlapping_entities(self):
        """Test extraction when entities overlap."""
        text = "João Silva, CPF 123.456.789-00, email: joao@email.com"
        entities = self.extractor.extract(text)
        
        # Should extract both entities
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        email_entities = [e for e in entities if e["type"] == "email"]
        
        assert len(cpf_entities) == 1
        assert len(email_entities) == 1
        
        # Check that positions don't overlap
        cpf_entity = cpf_entities[0]
        email_entity = email_entities[0]
        
        assert not (cpf_entity["start"] < email_entity["end"] and 
                   cpf_entity["end"] > email_entity["start"])
    
    def test_extract_large_text(self):
        """Test extraction in large text."""
        # Create a large text with multiple entities
        text = "João Silva, CPF 123.456.789-00, " * 1000
        text += "email: joao@email.com, " * 1000
        
        entities = self.extractor.extract(text)
        
        # Should extract all entities
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        email_entities = [e for e in entities if e["type"] == "email"]
        
        assert len(cpf_entities) == 1000
        assert len(email_entities) == 1000
    
    def test_extract_unicode_text(self):
        """Test extraction in Unicode text."""
        text = "João Silva, CPF 123.456.789-00, email: joão@email.com"
        entities = self.extractor.extract(text)
        
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        email_entities = [e for e in entities if e["type"] == "email"]
        
        assert len(cpf_entities) == 1
        assert len(email_entities) == 1
        assert email_entities[0]["value"] == "joão@email.com"
    
    def test_extract_performance(self):
        """Test extraction performance."""
        import time
        
        text = "João Silva, CPF 123.456.789-00, email: joao@email.com" * 100
        
        start_time = time.time()
        entities = self.extractor.extract(text)
        extraction_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert extraction_time < 1.0, f"Extraction too slow: {extraction_time}s"
        
        # Should extract all entities
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        email_entities = [e for e in entities if e["type"] == "email"]
        
        assert len(cpf_entities) == 100
        assert len(email_entities) == 100
    
    def test_extract_with_ner_model(self):
        """Test extraction using NER model."""
        text = "João Silva, CPF 123.456.789-00, mora em São Paulo."
        
        # Test with NER model enabled
        entities = self.extractor.extract(text, use_ner=True)
        
        # Should extract entities using both regex and NER
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        assert len(cpf_entities) == 1
        
        # Check that NER was used
        cpf_entity = cpf_entities[0]
        assert "ner_confidence" in cpf_entity
    
    def test_extract_custom_patterns(self):
        """Test extraction with custom patterns."""
        # Add custom pattern
        custom_patterns = {
            "custom_id": {
                "pattern": r"\bID:\s*(\d{6})\b",
                "type": "custom_id"
            }
        }
        
        text = "ID: 123456 e CPF: 123.456.789-00"
        entities = self.extractor.extract(text, custom_patterns=custom_patterns)
        
        # Should extract both custom and standard entities
        custom_entities = [e for e in entities if e["type"] == "custom_id"]
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        
        assert len(custom_entities) == 1
        assert len(cpf_entities) == 1
        assert custom_entities[0]["value"] == "123456"
    
    def test_extract_validation(self):
        """Test entity validation."""
        text = "CPF: 123.456.789-00 e CPF: 123.456.789-99"
        entities = self.extractor.extract(text, validate=True)
        
        # Should only extract valid entities
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        assert len(cpf_entities) == 1  # Only valid CPF
        assert cpf_entities[0]["value"] == "123.456.789-00"
    
    def test_extract_error_handling(self):
        """Test error handling in extraction."""
        # Test with None input
        with pytest.raises(ValueError):
            self.extractor.extract(None)
        
        # Test with empty string
        entities = self.extractor.extract("")
        assert len(entities) == 0
        
        # Test with non-string input
        with pytest.raises(ValueError):
            self.extractor.extract(123)
