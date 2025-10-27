"""
Integration tests for PII protection system
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from apps.pii_vault.app.services.vault import VaultService
from apps.pii_vault.app.services.extraction import PIIExtractor
from packages.pii.morph_engine import MorphEngine
from packages.pii.redaction import PIIRedactor


class TestPIIProtectionIntegration:
    """Test PII protection system integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.vault_service = VaultService()
        self.extractor = PIIExtractor()
        self.morph_engine = MorphEngine()
        self.redactor = PIIRedactor()
        self.tenant_id = "test-tenant-123"
        self.user_id = "test-user-456"
    
    @pytest.mark.asyncio
    async def test_full_pii_protection_workflow(self):
        """Test complete PII protection workflow."""
        # 1. Original text with PII
        original_text = "João Silva, CPF 123.456.789-00, email: joao@email.com, telefone: (11) 99999-9999"
        
        # 2. Extract PII
        entities = self.extractor.extract(original_text)
        assert len(entities) > 0
        
        # 3. Tokenize PII
        pii_tokens = {}
        for entity in entities:
            token_result = await self.vault_service.tokenize(
                value=entity["value"],
                scope=entity["type"],
                tenant_id=self.tenant_id
            )
            pii_tokens[entity["type"]] = token_result["token"]
        
        # 4. Morph text with tokens
        morphed_text = self.morph_engine.morph(original_text, pii_tokens)
        
        # 5. Verify PII is replaced with tokens
        assert "123.456.789-00" not in morphed_text
        assert "joao@email.com" not in morphed_text
        assert "(11) 99999-9999" not in morphed_text
        
        # 6. Detokenize for final document
        detokenized_values = {}
        for scope, token in pii_tokens.items():
            value = await self.vault_service.detokenize(
                token=token,
                tenant_id=self.tenant_id,
                purpose="test",
                actor_id=self.user_id
            )
            detokenized_values[scope] = value
        
        # 7. Verify detokenization works
        assert detokenized_values["cpf"] == "123.456.789-00"
        assert detokenized_values["email"] == "joao@email.com"
        assert detokenized_values["phone"] == "(11) 99999-9999"
    
    @pytest.mark.asyncio
    async def test_pii_protection_with_redaction(self):
        """Test PII protection with redaction fallback."""
        # 1. Original text with PII
        original_text = "João Silva, CPF 123.456.789-00, email: joao@email.com"
        
        # 2. Try to extract and tokenize PII
        entities = self.extractor.extract(original_text)
        
        if entities:
            # 3. Tokenize PII
            pii_tokens = {}
            for entity in entities:
                try:
                    token_result = await self.vault_service.tokenize(
                        value=entity["value"],
                        scope=entity["type"],
                        tenant_id=self.tenant_id
                    )
                    pii_tokens[entity["type"]] = token_result["token"]
                except Exception:
                    # Fallback to redaction
                    pii_tokens[entity["type"]] = f"[{entity['type'].upper()}_REDACTED]"
            
            # 4. Morph text
            morphed_text = self.morph_engine.morph(original_text, pii_tokens)
        else:
            # Fallback to redaction
            morphed_text = self.redactor.redact(original_text)
        
        # 5. Verify PII is protected
        assert "123.456.789-00" not in morphed_text
        assert "joao@email.com" not in morphed_text
    
    @pytest.mark.asyncio
    async def test_pii_protection_with_validation(self):
        """Test PII protection with validation."""
        # 1. Original text with valid and invalid PII
        original_text = "João Silva, CPF 123.456.789-00, CPF inválido: 123.456.789-99"
        
        # 2. Extract PII with validation
        entities = self.extractor.extract(original_text, validate=True)
        
        # 3. Should only extract valid PII
        valid_entities = [e for e in entities if e["type"] == "cpf"]
        assert len(valid_entities) == 1
        assert valid_entities[0]["value"] == "123.456.789-00"
        
        # 4. Tokenize valid PII
        pii_tokens = {}
        for entity in valid_entities:
            token_result = await self.vault_service.tokenize(
                value=entity["value"],
                scope=entity["type"],
                tenant_id=self.tenant_id
            )
            pii_tokens[entity["type"]] = token_result["token"]
        
        # 5. Morph text
        morphed_text = self.morph_engine.morph(original_text, pii_tokens)
        
        # 6. Verify only valid PII is replaced
        assert "123.456.789-00" not in morphed_text
        assert "123.456.789-99" in morphed_text  # Invalid CPF should remain
    
    @pytest.mark.asyncio
    async def test_pii_protection_with_confidence_threshold(self):
        """Test PII protection with confidence threshold."""
        # 1. Original text with PII
        original_text = "João Silva, CPF 123.456.789-00, email: joao@email.com"
        
        # 2. Extract PII with confidence threshold
        entities = self.extractor.extract(original_text, confidence_threshold=0.8)
        
        # 3. Should only extract high-confidence entities
        high_confidence_entities = [e for e in entities if e["confidence"] >= 0.8]
        
        # 4. Tokenize high-confidence PII
        pii_tokens = {}
        for entity in high_confidence_entities:
            token_result = await self.vault_service.tokenize(
                value=entity["value"],
                scope=entity["type"],
                tenant_id=self.tenant_id
            )
            pii_tokens[entity["type"]] = token_result["token"]
        
        # 5. Morph text
        morphed_text = self.morph_engine.morph(original_text, pii_tokens)
        
        # 6. Verify high-confidence PII is replaced
        assert "123.456.789-00" not in morphed_text
        assert "joao@email.com" not in morphed_text
    
    @pytest.mark.asyncio
    async def test_pii_protection_with_custom_patterns(self):
        """Test PII protection with custom patterns."""
        # 1. Original text with custom PII
        original_text = "ID: 123456, CPF: 123.456.789-00"
        
        # 2. Custom patterns
        custom_patterns = {
            "custom_id": {
                "pattern": r"\bID:\s*(\d{6})\b",
                "type": "custom_id"
            }
        }
        
        # 3. Extract PII with custom patterns
        entities = self.extractor.extract(original_text, custom_patterns=custom_patterns)
        
        # 4. Should extract both custom and standard PII
        custom_entities = [e for e in entities if e["type"] == "custom_id"]
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        
        assert len(custom_entities) == 1
        assert len(cpf_entities) == 1
        
        # 5. Tokenize all PII
        pii_tokens = {}
        for entity in entities:
            token_result = await self.vault_service.tokenize(
                value=entity["value"],
                scope=entity["type"],
                tenant_id=self.tenant_id
            )
            pii_tokens[entity["type"]] = token_result["token"]
        
        # 6. Morph text
        morphed_text = self.morph_engine.morph(original_text, pii_tokens)
        
        # 7. Verify all PII is replaced
        assert "123456" not in morphed_text
        assert "123.456.789-00" not in morphed_text
    
    @pytest.mark.asyncio
    async def test_pii_protection_with_audit_logging(self):
        """Test PII protection with audit logging."""
        # 1. Original text with PII
        original_text = "João Silva, CPF 123.456.789-00"
        
        # 2. Extract and tokenize PII
        entities = self.extractor.extract(original_text)
        pii_tokens = {}
        
        for entity in entities:
            token_result = await self.vault_service.tokenize(
                value=entity["value"],
                scope=entity["type"],
                tenant_id=self.tenant_id
            )
            pii_tokens[entity["type"]] = token_result["token"]
        
        # 3. Morph text
        morphed_text = self.morph_engine.morph(original_text, pii_tokens)
        
        # 4. Detokenize with audit logging
        detokenized_values = {}
        for scope, token in pii_tokens.items():
            value = await self.vault_service.detokenize(
                token=token,
                tenant_id=self.tenant_id,
                purpose="test_audit",
                actor_id=self.user_id
            )
            detokenized_values[scope] = value
        
        # 5. Verify detokenization works
        assert detokenized_values["cpf"] == "123.456.789-00"
        
        # Note: In a real scenario, we would verify that audit logs were created
        # This would require checking the database or audit service
    
    @pytest.mark.asyncio
    async def test_pii_protection_with_error_handling(self):
        """Test PII protection with error handling."""
        # 1. Original text with PII
        original_text = "João Silva, CPF 123.456.789-00, email: joao@email.com"
        
        # 2. Extract PII
        entities = self.extractor.extract(original_text)
        
        # 3. Tokenize PII with error handling
        pii_tokens = {}
        for entity in entities:
            try:
                token_result = await self.vault_service.tokenize(
                    value=entity["value"],
                    scope=entity["type"],
                    tenant_id=self.tenant_id
                )
                pii_tokens[entity["type"]] = token_result["token"]
            except Exception as e:
                # Fallback to redaction
                pii_tokens[entity["type"]] = f"[{entity['type'].upper()}_ERROR]"
        
        # 4. Morph text
        morphed_text = self.morph_engine.morph(original_text, pii_tokens)
        
        # 5. Verify PII is protected (either tokenized or redacted)
        assert "123.456.789-00" not in morphed_text
        assert "joao@email.com" not in morphed_text
    
    @pytest.mark.asyncio
    async def test_pii_protection_with_performance_monitoring(self):
        """Test PII protection with performance monitoring."""
        import time
        
        # 1. Original text with PII
        original_text = "João Silva, CPF 123.456.789-00, email: joao@email.com" * 100
        
        # 2. Monitor extraction performance
        start_time = time.time()
        entities = self.extractor.extract(original_text)
        extraction_time = time.time() - start_time
        
        # 3. Monitor tokenization performance
        start_time = time.time()
        pii_tokens = {}
        for entity in entities:
            token_result = await self.vault_service.tokenize(
                value=entity["value"],
                scope=entity["type"],
                tenant_id=self.tenant_id
            )
            pii_tokens[entity["type"]] = token_result["token"]
        tokenization_time = time.time() - start_time
        
        # 4. Monitor morphing performance
        start_time = time.time()
        morphed_text = self.morph_engine.morph(original_text, pii_tokens)
        morphing_time = time.time() - start_time
        
        # 5. Verify performance is acceptable
        assert extraction_time < 1.0, f"Extraction too slow: {extraction_time}s"
        assert tokenization_time < 2.0, f"Tokenization too slow: {tokenization_time}s"
        assert morphing_time < 1.0, f"Morphing too slow: {morphing_time}s"
        
        # 6. Verify PII is protected
        assert "123.456.789-00" not in morphed_text
        assert "joao@email.com" not in morphed_text
    
    @pytest.mark.asyncio
    async def test_pii_protection_with_concurrent_operations(self):
        """Test PII protection with concurrent operations."""
        import asyncio
        
        # 1. Multiple texts with PII
        texts = [
            "João Silva, CPF 123.456.789-00",
            "Maria Santos, CPF 987.654.321-00",
            "Pedro Costa, CPF 111.222.333-44"
        ]
        
        async def protect_text(text):
            # Extract PII
            entities = self.extractor.extract(text)
            
            # Tokenize PII
            pii_tokens = {}
            for entity in entities:
                token_result = await self.vault_service.tokenize(
                    value=entity["value"],
                    scope=entity["type"],
                    tenant_id=self.tenant_id
                )
                pii_tokens[entity["type"]] = token_result["token"]
            
            # Morph text
            morphed_text = self.morph_engine.morph(text, pii_tokens)
            
            return morphed_text
        
        # 2. Run concurrent protection
        tasks = [protect_text(text) for text in texts]
        results = await asyncio.gather(*tasks)
        
        # 3. Verify all texts are protected
        assert len(results) == 3
        
        for result in results:
            # Should not contain any CPF
            assert "123.456.789-00" not in result
            assert "987.654.321-00" not in result
            assert "111.222.333-44" not in result
    
    @pytest.mark.asyncio
    async def test_pii_protection_with_large_dataset(self):
        """Test PII protection with large dataset."""
        # 1. Create large dataset
        texts = []
        for i in range(1000):
            text = f"Pessoa {i}, CPF {i:011d}, email: pessoa{i}@email.com"
            texts.append(text)
        
        # 2. Process all texts
        protected_texts = []
        for text in texts:
            # Extract PII
            entities = self.extractor.extract(text)
            
            # Tokenize PII
            pii_tokens = {}
            for entity in entities:
                token_result = await self.vault_service.tokenize(
                    value=entity["value"],
                    scope=entity["type"],
                    tenant_id=self.tenant_id
                )
                pii_tokens[entity["type"]] = token_result["token"]
            
            # Morph text
            morphed_text = self.morph_engine.morph(text, pii_tokens)
            protected_texts.append(morphed_text)
        
        # 3. Verify all texts are protected
        assert len(protected_texts) == 1000
        
        # Check a few samples
        for i in range(0, 1000, 100):
            protected_text = protected_texts[i]
            original_text = texts[i]
            
            # Should not contain original PII
            assert f"CPF {i:011d}" not in protected_text
            assert f"pessoa{i}@email.com" not in protected_text
            
            # Should contain tokens
            assert "CPF" in protected_text
            assert "email" in protected_text
    
    @pytest.mark.asyncio
    async def test_pii_protection_with_validation_and_confidence(self):
        """Test PII protection with both validation and confidence threshold."""
        # 1. Original text with valid and invalid PII
        original_text = "João Silva, CPF 123.456.789-00, CPF inválido: 123.456.789-99, email: joao@email.com"
        
        # 2. Extract PII with validation and confidence threshold
        entities = self.extractor.extract(
            original_text, 
            validate=True, 
            confidence_threshold=0.8
        )
        
        # 3. Should only extract valid, high-confidence entities
        valid_high_confidence_entities = [
            e for e in entities 
            if e["confidence"] >= 0.8 and e["type"] == "cpf"
        ]
        
        # 4. Tokenize valid, high-confidence PII
        pii_tokens = {}
        for entity in valid_high_confidence_entities:
            token_result = await self.vault_service.tokenize(
                value=entity["value"],
                scope=entity["type"],
                tenant_id=self.tenant_id
            )
            pii_tokens[entity["type"]] = token_result["token"]
        
        # 5. Morph text
        morphed_text = self.morph_engine.morph(original_text, pii_tokens)
        
        # 6. Verify only valid, high-confidence PII is replaced
        assert "123.456.789-00" not in morphed_text  # Valid CPF
        assert "123.456.789-99" in morphed_text  # Invalid CPF should remain
        assert "joao@email.com" in morphed_text  # Email should remain (not CPF)
    
    @pytest.mark.asyncio
    async def test_pii_protection_with_custom_options(self):
        """Test PII protection with custom options."""
        # 1. Original text with PII
        original_text = "João Silva, CPF 123.456.789-00, email: joao@email.com"
        
        # 2. Extract PII with custom options
        entities = self.extractor.extract(
            original_text,
            custom_patterns={
                "custom_name": {
                    "pattern": r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b",
                    "type": "custom_name"
                }
            }
        )
        
        # 3. Should extract both custom and standard PII
        custom_entities = [e for e in entities if e["type"] == "custom_name"]
        cpf_entities = [e for e in entities if e["type"] == "cpf"]
        email_entities = [e for e in entities if e["type"] == "email"]
        
        assert len(custom_entities) == 1
        assert len(cpf_entities) == 1
        assert len(email_entities) == 1
        
        # 4. Tokenize all PII
        pii_tokens = {}
        for entity in entities:
            token_result = await self.vault_service.tokenize(
                value=entity["value"],
                scope=entity["type"],
                tenant_id=self.tenant_id
            )
            pii_tokens[entity["type"]] = token_result["token"]
        
        # 5. Morph text with custom options
        morphed_text = self.morph_engine.morph(
            original_text, 
            pii_tokens,
            preserve_case=True,
            preserve_punctuation=True
        )
        
        # 6. Verify all PII is replaced
        assert "João Silva" not in morphed_text
        assert "123.456.789-00" not in morphed_text
        assert "joao@email.com" not in morphed_text
        
        # 7. Verify custom options are preserved
        assert morphed_text.endswith(".")
        assert "," in morphed_text
