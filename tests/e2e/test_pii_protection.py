"""
End-to-end tests for PII protection system
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch


class TestPIIProtectionE2E:
    """Test PII protection system end-to-end."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.notarius_url = "http://localhost:8000"
        self.pii_vault_url = "http://localhost:8002"
        
        self.notarius_client = httpx.AsyncClient(base_url=self.notarius_url)
        self.pii_vault_client = httpx.AsyncClient(base_url=self.pii_vault_url)
        
        self.tenant_id = "test-tenant-123"
        self.user_id = "test-user-456"
    
    @pytest.mark.asyncio
    async def test_pii_protection_workflow(self):
        """Test complete PII protection workflow."""
        # 1. Generate minuta with PII
        command = "Fazer procuração para João Silva, CPF 123.456.789-00, email: joao@email.com, telefone: (11) 99999-9999"
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json={"command": command, "processo_id": None}
        )
        
        assert generate_response.status_code == 201
        generate_data = generate_response.json()
        minuta_id = generate_data["minuta_id"]
        
        # 2. Verify PII is tokenized in minuta
        minuta_response = await self.notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
        assert minuta_response.status_code == 200
        
        minuta_data = minuta_response.json()
        assert minuta_data["corpo_md"] is not None
        assert minuta_data["variaveis_json"] is not None
        
        # PII should be replaced with tokens in corpo_md
        corpo_md = minuta_data["corpo_md"]
        assert "123.456.789-00" not in corpo_md
        assert "joao@email.com" not in corpo_md
        assert "(11) 99999-9999" not in corpo_md
        
        # Should contain tokens
        assert "PARTY_1_CPF" in corpo_md or "CPF" in corpo_md
        assert "PARTY_1_EMAIL" in corpo_md or "EMAIL" in corpo_md
        assert "PARTY_1_PHONE" in corpo_md or "PHONE" in corpo_md
        
        # 3. Approve minuta
        approve_response = await self.notarius_client.post(
            f"/api/v1/notarius/minutas/{minuta_id}/approve/"
        )
        assert approve_response.status_code == 200
        
        # 4. Finalize minuta (should detokenize PII)
        finalize_response = await self.notarius_client.post(
            f"/api/v1/notarius/minutas/{minuta_id}/finalize/"
        )
        assert finalize_response.status_code == 200
        
        # 5. Download final document
        finalize_data = finalize_response.json()
        download_response = await self.notarius_client.get(finalize_data["download_url"])
        assert download_response.status_code == 200
        
        # Final document should contain real PII
        pdf_content = download_response.content
        assert len(pdf_content) > 0
        
        # Note: In a real scenario, we would parse the PDF and verify PII is present
        # For now, we'll just verify the document was generated successfully
    
    @pytest.mark.asyncio
    async def test_pii_vault_tokenization(self):
        """Test PII Vault tokenization directly."""
        # 1. Tokenize PII
        tokenize_payload = {
            "value": "João Silva",
            "scope": "name",
            "tenant_id": self.tenant_id
        }
        
        tokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/tokenize",
            json=tokenize_payload
        )
        
        assert tokenize_response.status_code == 200
        tokenize_data = tokenize_response.json()
        
        assert "token" in tokenize_data
        assert "hash" in tokenize_data
        assert tokenize_data["token"] != "João Silva"
        
        # 2. Detokenize PII
        detokenize_payload = {
            "token": tokenize_data["token"],
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "purpose": "test"
        }
        
        detokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/detokenize",
            json=detokenize_payload
        )
        
        assert detokenize_response.status_code == 200
        detokenize_data = detokenize_response.json()
        
        assert "value" in detokenize_data
        assert detokenize_data["value"] == "João Silva"
    
    @pytest.mark.asyncio
    async def test_pii_vault_batch_operations(self):
        """Test PII Vault batch operations."""
        # 1. Batch tokenize
        batch_payload = {
            "pii_entities": [
                {"value": "João Silva", "scope": "name"},
                {"value": "123.456.789-00", "scope": "cpf"},
                {"value": "joao@email.com", "scope": "email"}
            ],
            "tenant_id": self.tenant_id
        }
        
        batch_response = await self.pii_vault_client.post(
            "/api/v1/vault/batch-tokenize",
            json=batch_payload
        )
        
        assert batch_response.status_code == 200
        batch_data = batch_response.json()
        
        assert len(batch_data) == 3
        for item in batch_data:
            assert "token" in item
            assert "hash" in item
        
        # 2. Batch detokenize
        for item in batch_data:
            detokenize_payload = {
                "token": item["token"],
                "tenant_id": self.tenant_id,
                "user_id": self.user_id,
                "purpose": "test"
            }
            
            detokenize_response = await self.pii_vault_client.post(
                "/api/v1/vault/detokenize",
                json=detokenize_payload
            )
            
            assert detokenize_response.status_code == 200
            detokenize_data = detokenize_response.json()
            assert "value" in detokenize_data
    
    @pytest.mark.asyncio
    async def test_pii_vault_tenant_isolation(self):
        """Test PII Vault tenant isolation."""
        # 1. Tokenize for tenant 1
        tokenize_payload_1 = {
            "value": "João Silva",
            "scope": "name",
            "tenant_id": "tenant-1"
        }
        
        tokenize_response_1 = await self.pii_vault_client.post(
            "/api/v1/vault/tokenize",
            json=tokenize_payload_1
        )
        
        assert tokenize_response_1.status_code == 200
        token_1 = tokenize_response_1.json()["token"]
        
        # 2. Tokenize for tenant 2
        tokenize_payload_2 = {
            "value": "João Silva",
            "scope": "name",
            "tenant_id": "tenant-2"
        }
        
        tokenize_response_2 = await self.pii_vault_client.post(
            "/api/v1/vault/tokenize",
            json=tokenize_payload_2
        )
        
        assert tokenize_response_2.status_code == 200
        token_2 = tokenize_response_2.json()["token"]
        
        # 3. Tokens should be different
        assert token_1 != token_2
        
        # 4. Try to detokenize token_1 with tenant_2 (should fail)
        detokenize_payload = {
            "token": token_1,
            "tenant_id": "tenant-2",
            "user_id": self.user_id,
            "purpose": "test"
        }
        
        detokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/detokenize",
            json=detokenize_payload
        )
        
        # Should fail due to tenant isolation
        assert detokenize_response.status_code >= 400
    
    @pytest.mark.asyncio
    async def test_pii_vault_audit_logging(self):
        """Test PII Vault audit logging."""
        # 1. Tokenize PII
        tokenize_payload = {
            "value": "João Silva",
            "scope": "name",
            "tenant_id": self.tenant_id
        }
        
        tokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/tokenize",
            json=tokenize_payload
        )
        
        assert tokenize_response.status_code == 200
        token = tokenize_response.json()["token"]
        
        # 2. Detokenize PII
        detokenize_payload = {
            "token": token,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "purpose": "test_audit"
        }
        
        detokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/detokenize",
            json=detokenize_payload
        )
        
        assert detokenize_response.status_code == 200
        
        # Note: In a real scenario, we would verify that audit logs were created
        # This would require checking the database or audit service
    
    @pytest.mark.asyncio
    async def test_pii_vault_ttl_functionality(self):
        """Test PII Vault TTL functionality."""
        # 1. Tokenize with TTL
        tokenize_payload = {
            "value": "João Silva",
            "scope": "name",
            "tenant_id": self.tenant_id,
            "ttl_days": 1
        }
        
        tokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/tokenize",
            json=tokenize_payload
        )
        
        assert tokenize_response.status_code == 200
        token = tokenize_response.json()["token"]
        
        # 2. Should be able to detokenize immediately
        detokenize_payload = {
            "token": token,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "purpose": "test"
        }
        
        detokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/detokenize",
            json=detokenize_payload
        )
        
        assert detokenize_response.status_code == 200
        
        # Note: Testing actual TTL expiration would require time manipulation
        # which is complex in E2E tests. This would be better tested in integration tests.
    
    @pytest.mark.asyncio
    async def test_pii_vault_error_handling(self):
        """Test PII Vault error handling."""
        # 1. Test with invalid token
        detokenize_payload = {
            "token": "invalid-token",
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "purpose": "test"
        }
        
        detokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/detokenize",
            json=detokenize_payload
        )
        
        # Should return error
        assert detokenize_response.status_code >= 400
        
        # 2. Test with missing required fields
        tokenize_payload = {
            "value": "João Silva",
            "scope": "name"
            # Missing tenant_id
        }
        
        tokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/tokenize",
            json=tokenize_payload
        )
        
        # Should return validation error
        assert tokenize_response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_pii_vault_performance(self):
        """Test PII Vault performance."""
        import time
        
        # 1. Test single tokenization performance
        tokenize_payload = {
            "value": "João Silva",
            "scope": "name",
            "tenant_id": self.tenant_id
        }
        
        start_time = time.time()
        tokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/tokenize",
            json=tokenize_payload
        )
        tokenization_time = time.time() - start_time
        
        assert tokenize_response.status_code == 200
        assert tokenization_time < 1.0, f"Tokenization too slow: {tokenization_time}s"
        
        # 2. Test batch tokenization performance
        batch_payload = {
            "pii_entities": [
                {"value": f"Pessoa {i}", "scope": "name"}
                for i in range(100)
            ],
            "tenant_id": self.tenant_id
        }
        
        start_time = time.time()
        batch_response = await self.pii_vault_client.post(
            "/api/v1/vault/batch-tokenize",
            json=batch_payload
        )
        batch_time = time.time() - start_time
        
        assert batch_response.status_code == 200
        assert batch_time < 5.0, f"Batch tokenization too slow: {batch_time}s"
    
    @pytest.mark.asyncio
    async def test_pii_vault_concurrent_operations(self):
        """Test PII Vault concurrent operations."""
        import asyncio
        
        # 1. Test concurrent tokenization
        async def tokenize_value(i):
            payload = {
                "value": f"Pessoa {i}",
                "scope": "name",
                "tenant_id": self.tenant_id
            }
            return await self.pii_vault_client.post(
                "/api/v1/vault/tokenize",
                json=payload
            )
        
        # Run 10 concurrent tokenizations
        tasks = [tokenize_value(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            
            data = response.json()
            assert "token" in data
            assert "hash" in data
        
        # 2. Test concurrent detokenization
        tokens = [response.json()["token"] for response in responses]
        
        async def detokenize_value(token):
            payload = {
                "token": token,
                "tenant_id": self.tenant_id,
                "user_id": self.user_id,
                "purpose": "test"
            }
            return await self.pii_vault_client.post(
                "/api/v1/vault/detokenize",
                json=payload
            )
        
        # Run 10 concurrent detokenizations
        tasks = [detokenize_value(token) for token in tokens]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            
            data = response.json()
            assert "value" in data
    
    @pytest.mark.asyncio
    async def test_pii_vault_metrics_collection(self):
        """Test PII Vault metrics collection."""
        # 1. Make some requests
        tokenize_payload = {
            "value": "João Silva",
            "scope": "name",
            "tenant_id": self.tenant_id
        }
        
        for _ in range(5):
            await self.pii_vault_client.post(
                "/api/v1/vault/tokenize",
                json=tokenize_payload
            )
        
        # 2. Check metrics
        metrics_response = await self.pii_vault_client.get("/metrics")
        assert metrics_response.status_code == 200
        
        metrics_content = metrics_response.text
        assert "http_requests_total" in metrics_content
        assert "pii_vault_tokenize_duration_seconds" in metrics_content
        assert "pii_vault_detokenize_duration_seconds" in metrics_content
    
    @pytest.mark.asyncio
    async def test_pii_vault_health_check(self):
        """Test PII Vault health check."""
        # 1. Check health endpoint
        health_response = await self.pii_vault_client.get("/health")
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert "status" in health_data
        assert health_data["status"] == "healthy"
        
        # 2. Check that service is responsive
        tokenize_payload = {
            "value": "João Silva",
            "scope": "name",
            "tenant_id": self.tenant_id
        }
        
        tokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/tokenize",
            json=tokenize_payload
        )
        
        assert tokenize_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_pii_vault_security(self):
        """Test PII Vault security."""
        # 1. Test with invalid tenant
        tokenize_payload = {
            "value": "João Silva",
            "scope": "name",
            "tenant_id": "invalid-tenant"
        }
        
        tokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/tokenize",
            json=tokenize_payload
        )
        
        # Should handle invalid tenant gracefully
        assert tokenize_response.status_code in [200, 400, 403]
        
        # 2. Test with invalid user
        detokenize_payload = {
            "token": "test-token",
            "tenant_id": self.tenant_id,
            "user_id": "invalid-user",
            "purpose": "test"
        }
        
        detokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/detokenize",
            json=detokenize_payload
        )
        
        # Should handle invalid user gracefully
        assert detokenize_response.status_code in [200, 400, 403]
    
    @pytest.mark.asyncio
    async def test_pii_vault_validation(self):
        """Test PII Vault validation."""
        # 1. Test with empty value
        tokenize_payload = {
            "value": "",
            "scope": "name",
            "tenant_id": self.tenant_id
        }
        
        tokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/tokenize",
            json=tokenize_payload
        )
        
        # Should reject empty value
        assert tokenize_response.status_code == 422
        
        # 2. Test with invalid scope
        tokenize_payload = {
            "value": "João Silva",
            "scope": "",
            "tenant_id": self.tenant_id
        }
        
        tokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/tokenize",
            json=tokenize_payload
        )
        
        # Should reject invalid scope
        assert tokenize_response.status_code == 422
        
        # 3. Test with invalid tenant_id
        tokenize_payload = {
            "value": "João Silva",
            "scope": "name",
            "tenant_id": ""
        }
        
        tokenize_response = await self.pii_vault_client.post(
            "/api/v1/vault/tokenize",
            json=tokenize_payload
        )
        
        # Should reject invalid tenant_id
        assert tokenize_response.status_code == 422
