"""
Tests for PII morph engine.
"""
import pytest
from unittest.mock import patch, MagicMock
from packages.pii.morph_engine import MorphEngine


class TestMorphEngine:
    """Test cases for Morph Engine."""
    
    @pytest.fixture
    def morph_engine(self):
        """Create a Morph Engine instance."""
        return MorphEngine()
    
    def test_morph_cpf(self, morph_engine):
        """Test morphing CPF."""
        original = "123.456.789-00"
        morphed = morph_engine.morph(original, "cpf")
        
        assert morphed != original
        assert len(morphed) == len(original)
        assert morphed.count('.') == 2
        assert morphed.count('-') == 1
    
    def test_morph_cnpj(self, morph_engine):
        """Test morphing CNPJ."""
        original = "12.345.678/0001-90"
        morphed = morph_engine.morph(original, "cnpj")
        
        assert morphed != original
        assert len(morphed) == len(original)
        assert morphed.count('.') == 2
        assert morphed.count('/') == 1
        assert morphed.count('-') == 1
    
    def test_morph_email(self, morph_engine):
        """Test morphing email."""
        original = "user@example.com"
        morphed = morph_engine.morph(original, "email")
        
        assert morphed != original
        assert '@' in morphed
        assert '.' in morphed
    
    def test_morph_phone(self, morph_engine):
        """Test morphing phone."""
        original = "(21) 99999-9999"
        morphed = morph_engine.morph(original, "phone")
        
        assert morphed != original
        assert len(morphed) == len(original)
        assert morphed.count('(') == 1
        assert morphed.count(')') == 1
        assert morphed.count('-') == 1
    
    def test_morph_name(self, morph_engine):
        """Test morphing name."""
        original = "João Silva"
        morphed = morph_engine.morph(original, "name")
        
        assert morphed != original
        assert len(morphed.split()) == len(original.split())
    
    def test_morph_address(self, morph_engine):
        """Test morphing address."""
        original = "Rua das Flores, 123"
        morphed = morph_engine.morph(original, "address")
        
        assert morphed != original
        assert len(morphed) > 0
    
    def test_morph_unknown_type(self, morph_engine):
        """Test morphing unknown PII type."""
        original = "some text"
        morphed = morph_engine.morph(original, "unknown")
        
        # Should return original for unknown types
        assert morphed == original
    
    def test_morph_none_input(self, morph_engine):
        """Test morphing None input."""
        morphed = morph_engine.morph(None, "cpf")
        
        # Should handle None gracefully
        assert morphed is None
    
    def test_morph_empty_string(self, morph_engine):
        """Test morphing empty string."""
        morphed = morph_engine.morph("", "cpf")
        
        # Should return empty string
        assert morphed == ""
    
    def test_morph_deterministic(self, morph_engine):
        """Test that morphing is deterministic for same input."""
        original = "123.456.789-00"
        morphed1 = morph_engine.morph(original, "cpf")
        morphed2 = morph_engine.morph(original, "cpf")
        
        # Should be deterministic
        assert morphed1 == morphed2
    
    def test_morph_different_inputs(self, morph_engine):
        """Test that different inputs produce different morphs."""
        input1 = "123.456.789-00"
        input2 = "987.654.321-00"
        
        morphed1 = morph_engine.morph(input1, "cpf")
        morphed2 = morph_engine.morph(input2, "cpf")
        
        # Should be different
        assert morphed1 != morphed2
    
    def test_morph_preserves_format(self, morph_engine):
        """Test that morphing preserves format structure."""
        original = "123.456.789-00"
        morphed = morph_engine.morph(original, "cpf")
        
        # Should preserve CPF format: XXX.XXX.XXX-XX
        parts = morphed.split('-')
        assert len(parts) == 2
        assert len(parts[1]) == 2  # Check digits
        
        left_parts = parts[0].split('.')
        assert len(left_parts) == 3
        assert len(left_parts[0]) == 3
        assert len(left_parts[1]) == 3
        assert len(left_parts[2]) == 3
