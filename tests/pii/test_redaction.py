"""
Unit tests for PII redaction functionality
"""

import pytest
from packages.pii.redaction import PIIRedactor


class TestPIIRedactor:
    """Test PII redaction functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.redactor = PIIRedactor()
    
    def test_redact_cpf(self):
        """Test CPF redaction."""
        text = "João Silva, CPF 123.456.789-00, mora em São Paulo."
        redacted = self.redactor.redact(text)
        
        assert "123.456.789-00" not in redacted
        assert "***.***.***-**" in redacted or "[CPF_REDACTED]" in redacted
        assert "João Silva" in redacted  # Name should remain
    
    def test_redact_cnpj(self):
        """Test CNPJ redaction."""
        text = "Empresa ABC Ltda, CNPJ 12.345.678/0001-90, situada em São Paulo."
        redacted = self.redactor.redact(text)
        
        assert "12.345.678/0001-90" not in redacted
        assert "**.***.***/****-**" in redacted or "[CNPJ_REDACTED]" in redacted
        assert "Empresa ABC Ltda" in redacted  # Company name should remain
    
    def test_redact_email(self):
        """Test email redaction."""
        text = "Contato: joao.silva@email.com ou maria@empresa.com.br"
        redacted = self.redactor.redact(text)
        
        assert "joao.silva@email.com" not in redacted
        assert "maria@empresa.com.br" not in redacted
        assert "***@***.***" in redacted or "[EMAIL_REDACTED]" in redacted
    
    def test_redact_phone(self):
        """Test phone number redaction."""
        text = "Telefone: (11) 99999-9999 ou 11 3333-4444"
        redacted = self.redactor.redact(text)
        
        assert "(11) 99999-9999" not in redacted
        assert "11 3333-4444" not in redacted
        assert "***-****" in redacted or "[PHONE_REDACTED]" in redacted
    
    def test_redact_address(self):
        """Test address redaction."""
        text = "Endereço: Rua das Flores, 123, Bairro Centro, São Paulo - SP, CEP 01234-567"
        redacted = self.redactor.redact(text)
        
        assert "123" not in redacted
        assert "01234-567" not in redacted
        assert "***" in redacted or "[ADDRESS_REDACTED]" in redacted
        assert "São Paulo" in redacted  # City should remain
    
    def test_redact_cep(self):
        """Test CEP redaction."""
        text = "CEP 01234-567 ou 12345-678"
        redacted = self.redactor.redact(text)
        
        assert "01234-567" not in redacted
        assert "12345-678" not in redacted
        assert "***-**" in redacted or "[CEP_REDACTED]" in redacted
    
    def test_redact_multiple_entities(self):
        """Test redaction of multiple entity types."""
        text = """
        João Silva, CPF 123.456.789-00,
        email: joao@email.com,
        telefone: (11) 99999-9999,
        endereço: Rua das Flores, 123, São Paulo - SP, CEP 01234-567
        """
        
        redacted = self.redactor.redact(text)
        
        # Check that all PII is redacted
        assert "123.456.789-00" not in redacted
        assert "joao@email.com" not in redacted
        assert "(11) 99999-9999" not in redacted
        assert "123" not in redacted
        assert "01234-567" not in redacted
        
        # Check that non-PII remains
        assert "João Silva" in redacted
        assert "São Paulo" in redacted
        assert "Rua das Flores" in redacted
    
    def test_redact_no_pii(self):
        """Test redaction when no PII is present."""
        text = "Este é um texto sem informações pessoais."
        redacted = self.redactor.redact(text)
        
        assert redacted == text
    
    def test_redact_case_insensitive(self):
        """Test that redaction is case insensitive."""
        text = "CPF: 123.456.789-00 e cpf: 987.654.321-00"
        redacted = self.redactor.redact(text)
        
        assert "123.456.789-00" not in redacted
        assert "987.654.321-00" not in redacted
        assert "***.***.***-**" in redacted or "[CPF_REDACTED]" in redacted
    
    def test_redact_preserve_formatting(self):
        """Test that redaction preserves text formatting."""
        text = "João Silva, CPF 123.456.789-00, mora em São Paulo."
        redacted = self.redactor.redact(text)
        
        # Should preserve sentence structure
        assert redacted.endswith(".")
        assert "," in redacted
        assert "mora em São Paulo" in redacted
    
    def test_redact_custom_patterns(self):
        """Test redaction with custom patterns."""
        custom_patterns = {
            "custom_id": {
                "pattern": r"\bID:\s*(\d{6})\b",
                "replacement": "[ID_REDACTED]"
            }
        }
        
        text = "ID: 123456 e CPF: 123.456.789-00"
        redacted = self.redactor.redact(text, custom_patterns=custom_patterns)
        
        # Should redact both custom and standard patterns
        assert "123456" not in redacted
        assert "123.456.789-00" not in redacted
        assert "[ID_REDACTED]" in redacted
        assert "***.***.***-**" in redacted or "[CPF_REDACTED]" in redacted
    
    def test_redact_validation(self):
        """Test redaction with validation."""
        text = "CPF: 123.456.789-00 e CPF: 123.456.789-99"
        redacted = self.redactor.redact(text, validate=True)
        
        # Should only redact valid entities
        assert "123.456.789-00" not in redacted  # Valid CPF
        assert "123.456.789-99" in redacted  # Invalid CPF should remain
    
    def test_redact_confidence_threshold(self):
        """Test redaction with confidence threshold."""
        text = "CPF: 123.456.789-00 e CPF: 123.456.789-99"
        redacted = self.redactor.redact(text, confidence_threshold=0.9)
        
        # Should only redact high-confidence matches
        assert "123.456.789-00" not in redacted
        assert "123.456.789-99" in redacted
    
    def test_redact_large_text(self):
        """Test redaction in large text."""
        # Create large text with multiple PII occurrences
        text = "João Silva, CPF 123.456.789-00, " * 1000
        text += "email: joao@email.com, " * 1000
        
        redacted = self.redactor.redact(text)
        
        # Should redact all PII
        assert "123.456.789-00" not in redacted
        assert "joao@email.com" not in redacted
        
        # Should preserve non-PII
        assert "João Silva" in redacted
    
    def test_redact_performance(self):
        """Test redaction performance."""
        import time
        
        text = "João Silva, CPF 123.456.789-00, email: joao@email.com" * 100
        
        start_time = time.time()
        redacted = self.redactor.redact(text)
        redaction_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert redaction_time < 1.0, f"Redaction too slow: {redaction_time}s"
        
        # Should redact all PII
        assert "123.456.789-00" not in redacted
        assert "joao@email.com" not in redacted
    
    def test_redact_concurrent_operations(self):
        """Test concurrent redaction operations."""
        import asyncio
        
        async def redact_text(i):
            text = f"João Silva {i}, CPF 123.456.789-00"
            return self.redactor.redact(text)
        
        # Run 10 concurrent redactions
        tasks = [redact_text(i) for i in range(10)]
        results = asyncio.run(asyncio.gather(*tasks))
        
        # All should succeed
        assert len(results) == 10
        
        # All should have PII redacted
        for result in results:
            assert "123.456.789-00" not in result
            assert "***.***.***-**" in result or "[CPF_REDACTED]" in result
    
    def test_redact_error_handling(self):
        """Test error handling in redaction."""
        # Test with None input
        with pytest.raises(ValueError):
            self.redactor.redact(None)
        
        # Test with empty string
        redacted = self.redactor.redact("")
        assert redacted == ""
        
        # Test with non-string input
        with pytest.raises(ValueError):
            self.redactor.redact(123)
    
    def test_redact_statistics(self):
        """Test redaction statistics."""
        text = "João Silva, CPF 123.456.789-00, email: joao@email.com"
        
        redacted, stats = self.redactor.redact_with_stats(text)
        
        # Should redact PII
        assert "123.456.789-00" not in redacted
        assert "joao@email.com" not in redacted
        
        # Should return statistics
        assert "redactions" in stats
        assert "processing_time" in stats
        assert stats["redactions"] == 2
        assert stats["processing_time"] > 0
    
    def test_redact_custom_replacement(self):
        """Test redaction with custom replacement."""
        text = "CPF: 123.456.789-00"
        
        # Test with custom replacement
        redacted = self.redactor.redact(text, replacement="[PII_REDACTED]")
        
        assert "123.456.789-00" not in redacted
        assert "[PII_REDACTED]" in redacted
    
    def test_redact_partial_matches(self):
        """Test redaction with partial matches."""
        text = "João Silva comprou um carro de João."
        
        # Should not redact partial matches
        redacted = self.redactor.redact(text)
        
        assert "João Silva" in redacted  # Should remain
        assert "João" in redacted  # Should remain
    
    def test_redact_unicode_text(self):
        """Test redaction with Unicode text."""
        text = "João Silva, CPF 123.456.789-00, email: joão@email.com"
        
        redacted = self.redactor.redact(text)
        
        # Should handle Unicode correctly
        assert "123.456.789-00" not in redacted
        assert "joão@email.com" not in redacted
        assert "João Silva" in redacted
    
    def test_redact_special_characters(self):
        """Test redaction with special characters."""
        text = "João Silva (CPF: 123.456.789-00) comprou um carro."
        
        redacted = self.redactor.redact(text)
        
        # Should preserve special characters
        assert "(" in redacted
        assert ")" in redacted
        assert ":" in redacted
        assert "123.456.789-00" not in redacted
    
    def test_redact_multiple_occurrences(self):
        """Test redaction when PII appears multiple times."""
        text = "João Silva disse que João Silva comprou um carro."
        
        redacted = self.redactor.redact(text)
        
        # Should preserve all occurrences of name
        assert "João Silva" in redacted
        assert redacted.count("João Silva") == 2
    
    def test_redact_context_preservation(self):
        """Test that redaction preserves context."""
        text = "João Silva, CPF 123.456.789-00, mora em São Paulo."
        
        redacted = self.redactor.redact(text)
        
        # Should preserve context around PII
        assert "mora em São Paulo" in redacted
        assert "," in redacted
        assert redacted.endswith(".")
