"""
Unit tests for Morph Engine functionality
"""

import pytest
from packages.pii.morph_engine import MorphEngine


class TestMorphEngine:
    """Test Morph Engine functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.morph_engine = MorphEngine()
    
    def test_morph_simple_sentence(self):
        """Test morphing a simple sentence."""
        sentence = "João Silva comprou um carro."
        pii_map = {
            "PARTY_1_NAME": "João Silva"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        assert morphed != sentence
        assert "João Silva" not in morphed
        assert "PARTY_1_NAME" in morphed
    
    def test_morph_complex_sentence(self):
        """Test morphing a complex sentence."""
        sentence = "João Silva, CPF 123.456.789-00, comprou um carro de Maria Santos."
        pii_map = {
            "PARTY_1_NAME": "João Silva",
            "PARTY_1_CPF": "123.456.789-00",
            "PARTY_2_NAME": "Maria Santos"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        assert morphed != sentence
        assert "João Silva" not in morphed
        assert "123.456.789-00" not in morphed
        assert "Maria Santos" not in morphed
        assert "PARTY_1_NAME" in morphed
        assert "PARTY_1_CPF" in morphed
        assert "PARTY_2_NAME" in morphed
    
    def test_morph_preserve_grammar(self):
        """Test that morphing preserves grammar."""
        sentence = "João Silva comprou um carro."
        pii_map = {
            "PARTY_1_NAME": "João Silva"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        # Should preserve sentence structure
        assert morphed.endswith(".")
        assert "comprou" in morphed
        assert "um carro" in morphed
    
    def test_morph_preserve_punctuation(self):
        """Test that morphing preserves punctuation."""
        sentence = "João Silva, CPF 123.456.789-00, comprou um carro!"
        pii_map = {
            "PARTY_1_NAME": "João Silva",
            "PARTY_1_CPF": "123.456.789-00"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        # Should preserve punctuation
        assert morphed.endswith("!")
        assert "," in morphed
    
    def test_morph_preserve_case(self):
        """Test that morphing preserves case."""
        sentence = "JOÃO SILVA comprou um carro."
        pii_map = {
            "PARTY_1_NAME": "JOÃO SILVA"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        # Should preserve case
        assert morphed.startswith("PARTY_1_NAME")
        assert "comprou" in morphed.lower()
    
    def test_morph_multiple_occurrences(self):
        """Test morphing when PII appears multiple times."""
        sentence = "João Silva disse que João Silva comprou um carro."
        pii_map = {
            "PARTY_1_NAME": "João Silva"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        # Should replace all occurrences
        assert "João Silva" not in morphed
        assert morphed.count("PARTY_1_NAME") == 2
    
    def test_morph_partial_matches(self):
        """Test morphing with partial matches."""
        sentence = "João Silva comprou um carro de João."
        pii_map = {
            "PARTY_1_NAME": "João Silva"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        # Should only replace exact matches
        assert "João Silva" not in morphed
        assert "João" in morphed  # Partial match should remain
    
    def test_morph_case_insensitive(self):
        """Test morphing with case insensitive matching."""
        sentence = "joão silva comprou um carro."
        pii_map = {
            "PARTY_1_NAME": "João Silva"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        # Should replace case insensitive match
        assert "joão silva" not in morphed
        assert "PARTY_1_NAME" in morphed
    
    def test_morph_with_context(self):
        """Test morphing with context preservation."""
        sentence = "João Silva, CPF 123.456.789-00, comprou um carro."
        pii_map = {
            "PARTY_1_NAME": "João Silva",
            "PARTY_1_CPF": "123.456.789-00"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        # Should preserve context around PII
        assert "comprou um carro" in morphed
        assert "," in morphed
    
    def test_morph_empty_pii_map(self):
        """Test morphing with empty PII map."""
        sentence = "João Silva comprou um carro."
        pii_map = {}
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        # Should return original sentence
        assert morphed == sentence
    
    def test_morph_no_matches(self):
        """Test morphing when no PII matches are found."""
        sentence = "Este é um texto sem PII."
        pii_map = {
            "PARTY_1_NAME": "João Silva"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        # Should return original sentence
        assert morphed == sentence
    
    def test_morph_special_characters(self):
        """Test morphing with special characters."""
        sentence = "João Silva (CPF: 123.456.789-00) comprou um carro."
        pii_map = {
            "PARTY_1_NAME": "João Silva",
            "PARTY_1_CPF": "123.456.789-00"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        # Should preserve special characters
        assert "(" in morphed
        assert ")" in morphed
        assert ":" in morphed
        assert "João Silva" not in morphed
        assert "123.456.789-00" not in morphed
    
    def test_morph_unicode_text(self):
        """Test morphing with Unicode text."""
        sentence = "João Silva comprou um carro."
        pii_map = {
            "PARTY_1_NAME": "João Silva"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        # Should handle Unicode correctly
        assert "João Silva" not in morphed
        assert "PARTY_1_NAME" in morphed
    
    def test_morph_large_text(self):
        """Test morphing large text."""
        # Create large text with multiple PII occurrences
        sentence = "João Silva, CPF 123.456.789-00, " * 1000
        sentence += "comprou um carro."
        
        pii_map = {
            "PARTY_1_NAME": "João Silva",
            "PARTY_1_CPF": "123.456.789-00"
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map)
        
        # Should replace all occurrences
        assert "João Silva" not in morphed
        assert "123.456.789-00" not in morphed
        assert morphed.count("PARTY_1_NAME") == 1000
        assert morphed.count("PARTY_1_CPF") == 1000
    
    def test_morph_performance(self):
        """Test morphing performance."""
        import time
        
        sentence = "João Silva, CPF 123.456.789-00, " * 100
        pii_map = {
            "PARTY_1_NAME": "João Silva",
            "PARTY_1_CPF": "123.456.789-00"
        }
        
        start_time = time.time()
        morphed = self.morph_engine.morph(sentence, pii_map)
        morph_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert morph_time < 1.0, f"Morphing too slow: {morph_time}s"
        
        # Should replace all occurrences
        assert morphed.count("PARTY_1_NAME") == 100
        assert morphed.count("PARTY_1_CPF") == 100
    
    def test_morph_concurrent_operations(self):
        """Test concurrent morphing operations."""
        import asyncio
        
        async def morph_sentence(i):
            sentence = f"João Silva {i} comprou um carro."
            pii_map = {"PARTY_1_NAME": f"João Silva {i}"}
            return self.morph_engine.morph(sentence, pii_map)
        
        # Run 10 concurrent morphing operations
        tasks = [morph_sentence(i) for i in range(10)]
        results = asyncio.run(asyncio.gather(*tasks))
        
        # All should succeed
        assert len(results) == 10
        
        # All should have PII replaced
        for result in results:
            assert "João Silva" not in result
            assert "PARTY_1_NAME" in result
    
    def test_morph_error_handling(self):
        """Test error handling in morphing."""
        # Test with None input
        with pytest.raises(ValueError):
            self.morph_engine.morph(None, {})
        
        # Test with empty string
        morphed = self.morph_engine.morph("", {})
        assert morphed == ""
        
        # Test with non-string input
        with pytest.raises(ValueError):
            self.morph_engine.morph(123, {})
        
        # Test with None PII map
        with pytest.raises(ValueError):
            self.morph_engine.morph("João Silva", None)
    
    def test_morph_validation(self):
        """Test morphing validation."""
        sentence = "João Silva comprou um carro."
        pii_map = {
            "PARTY_1_NAME": "João Silva"
        }
        
        # Test with validation enabled
        morphed = self.morph_engine.morph(sentence, pii_map, validate=True)
        
        # Should replace PII
        assert "João Silva" not in morphed
        assert "PARTY_1_NAME" in morphed
        
        # Test with validation disabled
        morphed_no_validation = self.morph_engine.morph(sentence, pii_map, validate=False)
        
        # Should also replace PII
        assert "João Silva" not in morphed_no_validation
        assert "PARTY_1_NAME" in morphed_no_validation
    
    def test_morph_custom_options(self):
        """Test morphing with custom options."""
        sentence = "João Silva comprou um carro."
        pii_map = {
            "PARTY_1_NAME": "João Silva"
        }
        
        # Test with custom options
        options = {
            "preserve_case": True,
            "preserve_punctuation": True
        }
        
        morphed = self.morph_engine.morph(sentence, pii_map, **options)
        
        # Should replace PII with custom options
        assert "João Silva" not in morphed
        assert "PARTY_1_NAME" in morphed
        assert morphed.endswith(".")
    
    def test_morph_statistics(self):
        """Test morphing statistics."""
        sentence = "João Silva, CPF 123.456.789-00, comprou um carro."
        pii_map = {
            "PARTY_1_NAME": "João Silva",
            "PARTY_1_CPF": "123.456.789-00"
        }
        
        morphed, stats = self.morph_engine.morph_with_stats(sentence, pii_map)
        
        # Should replace PII
        assert "João Silva" not in morphed
        assert "123.456.789-00" not in morphed
        
        # Should return statistics
        assert "replacements" in stats
        assert "processing_time" in stats
        assert stats["replacements"] == 2
        assert stats["processing_time"] > 0
