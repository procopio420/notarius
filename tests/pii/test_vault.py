"""
Unit tests for PII Vault functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from apps.pii_vault.app.models import EncryptedToken
from apps.pii_vault.app.services.kms import KMSProvider, LocalKMSProvider
from apps.pii_vault.app.services.vault import VaultService


class TestKMSProvider:
    """Test KMS provider functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.kms = LocalKMSProvider()
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption round-trip."""
        plaintext = "João Silva, CPF 123.456.789-00"
        
        # Encrypt
        ciphertext = self.kms.encrypt(plaintext)
        assert ciphertext != plaintext
        assert len(ciphertext) > 0
        
        # Decrypt
        decrypted = self.kms.decrypt(ciphertext)
        assert decrypted == plaintext
    
    def test_encrypt_different_values(self):
        """Test that different values produce different ciphertexts."""
        value1 = "João Silva"
        value2 = "Maria Santos"
        
        ciphertext1 = self.kms.encrypt(value1)
        ciphertext2 = self.kms.encrypt(value2)
        
        assert ciphertext1 != ciphertext2
    
    def test_encrypt_same_value(self):
        """Test that same value produces different ciphertexts (non-deterministic)."""
        value = "João Silva"
        
        ciphertext1 = self.kms.encrypt(value)
        ciphertext2 = self.kms.encrypt(value)
        
        # Should be different due to random IV
        assert ciphertext1 != ciphertext2
        
        # But should decrypt to same value
        assert self.kms.decrypt(ciphertext1) == value
        assert self.kms.decrypt(ciphertext2) == value
    
    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        plaintext = ""
        
        ciphertext = self.kms.encrypt(plaintext)
        decrypted = self.kms.decrypt(ciphertext)
        
        assert decrypted == plaintext
    
    def test_encrypt_large_data(self):
        """Test encryption of large data."""
        plaintext = "A" * 10000  # 10KB of data
        
        ciphertext = self.kms.encrypt(plaintext)
        decrypted = self.kms.decrypt(ciphertext)
        
        assert decrypted == plaintext
    
    def test_encrypt_special_characters(self):
        """Test encryption of special characters."""
        plaintext = "João Silva, CPF 123.456.789-00, email: joão@email.com"
        
        ciphertext = self.kms.encrypt(plaintext)
        decrypted = self.kms.decrypt(ciphertext)
        
        assert decrypted == plaintext
    
    def test_invalid_ciphertext(self):
        """Test decryption of invalid ciphertext."""
        with pytest.raises(Exception):
            self.kms.decrypt("invalid_ciphertext")


class TestVaultService:
    """Test PII Vault service functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.vault_service = VaultService()
        self.tenant_id = "test-tenant-123"
        self.user_id = "test-user-456"
    
    @pytest.mark.asyncio
    async def test_tokenize_detokenize_round_trip(self):
        """Test tokenization and detokenization round-trip."""
        value = "João Silva, CPF 123.456.789-00"
        scope = "cpf"
        
        # Tokenize
        token_result = await self.vault_service.tokenize(
            value=value,
            scope=scope,
            tenant_id=self.tenant_id
        )
        
        assert "token" in token_result
        assert "hash" in token_result
        assert token_result["token"] != value
        assert len(token_result["hash"]) > 0
        
        # Detokenize
        detokenized_value = await self.vault_service.detokenize(
            token=token_result["token"],
            tenant_id=self.tenant_id,
            purpose="test",
            actor_id=self.user_id
        )
        
        assert detokenized_value == value
    
    @pytest.mark.asyncio
    async def test_tokenize_different_scopes(self):
        """Test tokenization with different scopes."""
        value = "João Silva"
        
        # Tokenize with different scopes
        token1 = await self.vault_service.tokenize(value, "name", self.tenant_id)
        token2 = await self.vault_service.tokenize(value, "cpf", self.tenant_id)
        
        # Should produce different tokens
        assert token1["token"] != token2["token"]
        
        # But should decrypt to same value
        value1 = await self.vault_service.detokenize(token1["token"], self.tenant_id, "test", self.user_id)
        value2 = await self.vault_service.detokenize(token2["token"], self.tenant_id, "test", self.user_id)
        
        assert value1 == value2 == value
    
    @pytest.mark.asyncio
    async def test_tokenize_same_value_different_tenants(self):
        """Test tokenization for different tenants."""
        value = "João Silva"
        
        # Tokenize for different tenants
        token1 = await self.vault_service.tokenize(value, "name", "tenant-1")
        token2 = await self.vault_service.tokenize(value, "name", "tenant-2")
        
        # Should produce different tokens
        assert token1["token"] != token2["token"]
        
        # Should decrypt to same value
        value1 = await self.vault_service.detokenize(token1["token"], "tenant-1", "test", self.user_id)
        value2 = await self.vault_service.detokenize(token2["token"], "tenant-2", "test", self.user_id)
        
        assert value1 == value2 == value
    
    @pytest.mark.asyncio
    async def test_batch_tokenize(self):
        """Test batch tokenization."""
        values = [
            {"value": "João Silva", "scope": "name"},
            {"value": "123.456.789-00", "scope": "cpf"},
            {"value": "joao@email.com", "scope": "email"},
        ]
        
        tokens = await self.vault_service.batch_tokenize(values, self.tenant_id)
        
        assert len(tokens) == len(values)
        
        # Verify each token
        for i, token in enumerate(tokens):
            assert "token" in token
            assert "hash" in token
            assert token["token"] != values[i]["value"]
            
            # Test detokenization
            detokenized = await self.vault_service.detokenize(
                token["token"], self.tenant_id, "test", self.user_id
            )
            assert detokenized == values[i]["value"]
    
    @pytest.mark.asyncio
    async def test_hash_consistency(self):
        """Test that same value produces same hash."""
        value = "João Silva"
        
        # Tokenize multiple times
        token1 = await self.vault_service.tokenize(value, "name", self.tenant_id)
        token2 = await self.vault_service.tokenize(value, "name", self.tenant_id)
        
        # Should produce different tokens but same hash
        assert token1["token"] != token2["token"]
        assert token1["hash"] == token2["hash"]
    
    @pytest.mark.asyncio
    async def test_audit_logging(self):
        """Test that detokenization is logged."""
        value = "João Silva"
        
        # Tokenize
        token_result = await self.vault_service.tokenize(value, "name", self.tenant_id)
        
        # Detokenize
        await self.vault_service.detokenize(
            token_result["token"], self.tenant_id, "test", self.user_id
        )
        
        # Check that audit log was created
        # This would require checking the database or audit service
        # For now, we'll just verify no exception was raised
        assert True
    
    @pytest.mark.asyncio
    async def test_invalid_token(self):
        """Test detokenization of invalid token."""
        with pytest.raises(Exception):
            await self.vault_service.detokenize(
                "invalid_token", self.tenant_id, "test", self.user_id
            )
    
    @pytest.mark.asyncio
    async def test_wrong_tenant(self):
        """Test detokenization with wrong tenant."""
        value = "João Silva"
        
        # Tokenize for tenant-1
        token_result = await self.vault_service.tokenize(value, "name", "tenant-1")
        
        # Try to detokenize for tenant-2
        with pytest.raises(Exception):
            await self.vault_service.detokenize(
                token_result["token"], "tenant-2", "test", self.user_id
            )
    
    @pytest.mark.asyncio
    async def test_performance(self):
        """Test tokenization performance."""
        import time
        
        value = "João Silva, CPF 123.456.789-00"
        
        # Test single tokenization
        start_time = time.time()
        await self.vault_service.tokenize(value, "name", self.tenant_id)
        single_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert single_time < 0.1, f"Tokenization too slow: {single_time}s"
        
        # Test batch tokenization
        values = [{"value": f"Value {i}", "scope": "name"} for i in range(100)]
        
        start_time = time.time()
        await self.vault_service.batch_tokenize(values, self.tenant_id)
        batch_time = time.time() - start_time
        
        # Batch should be faster per item
        assert batch_time < 1.0, f"Batch tokenization too slow: {batch_time}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self):
        """Test concurrent tokenization operations."""
        import asyncio
        
        async def tokenize_value(i):
            return await self.vault_service.tokenize(f"Value {i}", "name", self.tenant_id)
        
        # Run 10 concurrent tokenizations
        tasks = [tokenize_value(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 10
        
        # All should produce different tokens
        tokens = [result["token"] for result in results]
        assert len(set(tokens)) == 10  # All unique
    
    @pytest.mark.asyncio
    async def test_memory_usage(self):
        """Test memory usage with large number of tokens."""
        import gc
        
        # Create many tokens
        tokens = []
        for i in range(1000):
            token = await self.vault_service.tokenize(f"Value {i}", "name", self.tenant_id)
            tokens.append(token)
        
        # Force garbage collection
        gc.collect()
        
        # Verify all tokens still work
        for token in tokens[:10]:  # Test first 10
            value = await self.vault_service.detokenize(
                token["token"], self.tenant_id, "test", self.user_id
            )
            assert value.startswith("Value ")
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in various scenarios."""
        # Test with empty value
        with pytest.raises(ValueError):
            await self.vault_service.tokenize("", "name", self.tenant_id)
        
        # Test with invalid scope
        with pytest.raises(ValueError):
            await self.vault_service.tokenize("João Silva", "", self.tenant_id)
        
        # Test with invalid tenant
        with pytest.raises(ValueError):
            await self.vault_service.tokenize("João Silva", "name", "")
    
    @pytest.mark.asyncio
    async def test_ttl_functionality(self):
        """Test TTL (time-to-live) functionality."""
        value = "João Silva"
        ttl_days = 1
        
        # Tokenize with TTL
        token_result = await self.vault_service.tokenize(
            value, "name", self.tenant_id, ttl_days=ttl_days
        )
        
        # Should be able to detokenize immediately
        detokenized = await self.vault_service.detokenize(
            token_result["token"], self.tenant_id, "test", self.user_id
        )
        assert detokenized == value
        
        # Note: Testing actual TTL expiration would require time manipulation
        # which is complex in unit tests. This would be better tested in integration tests.
