"""
Unit tests for PII extraction functionality
"""

import pytest
import re
from packages.pii.extractors import PIIExtractor, PIIEntity


class TestPIIExtractor:
    """Test PII extraction functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = PIIExtractor()
    
    def test_cpf_extraction(self):
        """Test CPF extraction with various formats."""
        test_cases = [
            ("João Silva, CPF 123.456.789-00", "123.456.789-00"),
            ("CPF: 98765432100", "98765432100"),
            ("Documento 111.222.333-44 válido", "111.222.333-44"),
            ("CPF 12345678901 sem formatação", "12345678901"),
        ]
        
        for text, expected_cpf in test_cases:
            entities = self.extractor.extract_cpf(text)
            assert len(entities) > 0, f"No CPF found in: {text}"
            assert entities[0].value == expected_cpf, f"Expected {expected_cpf}, got {entities[0].value}"
            assert entities[0].type == "cpf"
            assert entities[0].confidence > 0.8
    
    def test_cnpj_extraction(self):
        """Test CNPJ extraction with various formats."""
        test_cases = [
            ("Empresa ABC Ltda, CNPJ 12.345.678/0001-90", "12.345.678/0001-90"),
            ("CNPJ: 98765432000123", "98765432000123"),
            ("Documento 11.222.333/0001-44 válido", "11.222.333/0001-44"),
        ]
        
        for text, expected_cnpj in test_cases:
            entities = self.extractor.extract_cnpj(text)
            assert len(entities) > 0, f"No CNPJ found in: {text}"
            assert entities[0].value == expected_cnpj, f"Expected {expected_cnpj}, got {entities[0].value}"
            assert entities[0].type == "cnpj"
            assert entities[0].confidence > 0.8
    
    def test_name_extraction(self):
        """Test name extraction using NER."""
        test_cases = [
            ("João Silva está presente", "João Silva"),
            ("Maria dos Santos trabalha aqui", "Maria dos Santos"),
            ("Pedro Oliveira e Ana Costa", ["Pedro Oliveira", "Ana Costa"]),
        ]
        
        for text, expected_names in test_cases:
            entities = self.extractor.extract_names(text)
            if isinstance(expected_names, str):
                expected_names = [expected_names]
            
            assert len(entities) >= len(expected_names), f"Expected at least {len(expected_names)} names in: {text}"
            
            extracted_names = [entity.value for entity in entities]
            for expected_name in expected_names:
                assert any(expected_name in name for name in extracted_names), f"Expected {expected_name} in {extracted_names}"
    
    def test_email_extraction(self):
        """Test email extraction."""
        test_cases = [
            ("Contato: joao@email.com", "joao@email.com"),
            ("Email: maria.silva@empresa.com.br", "maria.silva@empresa.com.br"),
            ("Enviar para pedro@teste.org", "pedro@teste.org"),
        ]
        
        for text, expected_email in test_cases:
            entities = self.extractor.extract_emails(text)
            assert len(entities) > 0, f"No email found in: {text}"
            assert entities[0].value == expected_email, f"Expected {expected_email}, got {entities[0].value}"
            assert entities[0].type == "email"
    
    def test_phone_extraction(self):
        """Test phone number extraction."""
        test_cases = [
            ("Telefone: (11) 99999-9999", "(11) 99999-9999"),
            ("Cel: 11987654321", "11987654321"),
            ("Fone: +55 11 3333-4444", "+55 11 3333-4444"),
        ]
        
        for text, expected_phone in test_cases:
            entities = self.extractor.extract_phones(text)
            assert len(entities) > 0, f"No phone found in: {text}"
            assert entities[0].value == expected_phone, f"Expected {expected_phone}, got {entities[0].value}"
            assert entities[0].type == "phone"
    
    def test_address_extraction(self):
        """Test address extraction."""
        test_cases = [
            ("Endereço: Rua das Flores, 123, São Paulo", "Rua das Flores, 123, São Paulo"),
            ("Morando na Av. Paulista, 1000", "Av. Paulista, 1000"),
        ]
        
        for text, expected_address in test_cases:
            entities = self.extractor.extract_addresses(text)
            assert len(entities) > 0, f"No address found in: {text}"
            assert entities[0].value == expected_address, f"Expected {expected_address}, got {entities[0].value}"
            assert entities[0].type == "address"
    
    def test_comprehensive_extraction(self):
        """Test comprehensive PII extraction."""
        text = """
        João Silva, CPF 123.456.789-00, 
        email: joao@email.com, 
        telefone: (11) 99999-9999,
        endereço: Rua das Flores, 123, São Paulo.
        """
        
        entities = self.extractor.extract_all(text)
        
        # Check that all types of PII are found
        entity_types = {entity.type for entity in entities}
        expected_types = {"cpf", "email", "phone", "address", "name"}
        
        assert entity_types.issuperset(expected_types), f"Expected {expected_types}, got {entity_types}"
        
        # Check specific values
        cpf_entity = next((e for e in entities if e.type == "cpf"), None)
        assert cpf_entity is not None
        assert cpf_entity.value == "123.456.789-00"
        
        email_entity = next((e for e in entities if e.type == "email"), None)
        assert email_entity is not None
        assert email_entity.value == "joao@email.com"
    
    def test_extraction_confidence(self):
        """Test that extraction confidence is reasonable."""
        text = "João Silva, CPF 123.456.789-00"
        
        entities = self.extractor.extract_all(text)
        
        for entity in entities:
            assert 0.0 <= entity.confidence <= 1.0, f"Invalid confidence: {entity.confidence}"
            assert entity.confidence > 0.5, f"Low confidence: {entity.confidence}"
    
    def test_extraction_positions(self):
        """Test that extraction positions are correct."""
        text = "João Silva, CPF 123.456.789-00"
        
        entities = self.extractor.extract_all(text)
        
        for entity in entities:
            assert 0 <= entity.start < entity.end <= len(text), f"Invalid positions: {entity.start}-{entity.end}"
            assert text[entity.start:entity.end] == entity.value, f"Position mismatch: {text[entity.start:entity.end]} != {entity.value}"
    
    def test_no_false_positives(self):
        """Test that extraction doesn't produce false positives."""
        text = "Este é um texto sem PII. Apenas palavras comuns."
        
        entities = self.extractor.extract_all(text)
        
        # Should not extract any PII from this text
        assert len(entities) == 0, f"False positives detected: {entities}"
    
    def test_edge_cases(self):
        """Test edge cases in PII extraction."""
        # Empty text
        entities = self.extractor.extract_all("")
        assert len(entities) == 0
        
        # Text with only numbers
        entities = self.extractor.extract_all("123456789")
        assert len(entities) == 0  # Should not extract random numbers as CPF
        
        # Text with partial matches
        entities = self.extractor.extract_all("123.456.789")  # Incomplete CPF
        assert len(entities) == 0
        
        # Text with multiple similar patterns
        text = "CPF 123.456.789-00 e CNPJ 12.345.678/0001-90"
        entities = self.extractor.extract_all(text)
        assert len(entities) == 2
        assert any(e.type == "cpf" for e in entities)
        assert any(e.type == "cnpj" for e in entities)
    
    def test_performance(self):
        """Test extraction performance."""
        import time
        
        # Large text with multiple PII instances
        text = "João Silva, CPF 123.456.789-00, email: joao@email.com. " * 100
        
        start_time = time.time()
        entities = self.extractor.extract_all(text)
        end_time = time.time()
        
        # Should complete within reasonable time (less than 1 second)
        assert end_time - start_time < 1.0, f"Extraction too slow: {end_time - start_time}s"
        
        # Should find multiple instances
        assert len(entities) > 100, f"Expected many entities, got {len(entities)}"
    
    def test_extraction_coverage(self):
        """Test that extraction covers expected percentage of PII."""
        test_texts = [
            "João Silva, CPF 123.456.789-00",
            "Maria Santos, email: maria@email.com",
            "Pedro Oliveira, telefone: (11) 99999-9999",
            "Ana Costa, endereço: Rua das Flores, 123",
            "Empresa ABC, CNPJ 12.345.678/0001-90",
        ]
        
        total_expected = 0
        total_found = 0
        
        for text in test_texts:
            entities = self.extractor.extract_all(text)
            total_found += len(entities)
            total_expected += 1  # Each text should have at least one PII
        
        coverage = total_found / total_expected if total_expected > 0 else 0
        assert coverage >= 0.95, f"PII extraction coverage too low: {coverage:.2%}"
