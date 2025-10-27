"""
End-to-end tests for Notarius integration
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch


class TestNotariusIntegrationE2E:
    """Test Notarius integration end-to-end."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.notarius_url = "http://localhost:8000"
        self.notarius_client = httpx.AsyncClient(base_url=self.notarius_url)
    
    @pytest.mark.asyncio
    async def test_notarius_health_check(self):
        """Test Notarius health check."""
        # 1. Check health endpoint
        health_response = await self.notarius_client.get("/health")
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert "status" in health_data
        assert health_data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_notarius_metrics_collection(self):
        """Test Notarius metrics collection."""
        # 1. Make some requests
        generate_payload = {
            "command": "Fazer procuração para João Silva",
            "processo_id": None
        }
        
        for _ in range(5):
            await self.notarius_client.post(
                "/api/v1/notarius/ai/generate/",
                json=generate_payload
            )
        
        # 2. Check metrics
        metrics_response = await self.notarius_client.get("/metrics")
        assert metrics_response.status_code == 200
        
        metrics_content = metrics_response.text
        assert "http_requests_total" in metrics_content
        assert "ai_draft_generation_duration_seconds" in metrics_content
        assert "pii_vault_tokenize_duration_seconds" in metrics_content
        assert "lexnode_retrieval_duration_seconds" in metrics_content
        assert "intent_engine_parse_duration_seconds" in metrics_content
    
    @pytest.mark.asyncio
    async def test_notarius_error_handling(self):
        """Test Notarius error handling."""
        # 1. Test with invalid command
        generate_payload = {
            "command": "",
            "processo_id": None
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        # Should return error
        assert generate_response.status_code >= 400
        
        # 2. Test with invalid processo_id
        generate_payload = {
            "command": "Fazer procuração para João Silva",
            "processo_id": "invalid-uuid"
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        # Should return error
        assert generate_response.status_code >= 400
        
        # 3. Test with non-existent processo_id
        generate_payload = {
            "command": "Fazer procuração para João Silva",
            "processo_id": "00000000-0000-0000-0000-000000000000"
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        # Should return error
        assert generate_response.status_code >= 400
    
    @pytest.mark.asyncio
    async def test_notarius_performance(self):
        """Test Notarius performance."""
        import time
        
        # 1. Test generation performance
        generate_payload = {
            "command": "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em SP.",
            "processo_id": None
        }
        
        start_time = time.time()
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        generation_time = time.time() - start_time
        
        assert generate_response.status_code == 201
        assert generation_time < 30.0, f"Generation too slow: {generation_time}s"
        
        # 2. Test approval performance
        minuta_id = generate_response.json()["minuta_id"]
        
        start_time = time.time()
        approve_response = await self.notarius_client.post(
            f"/api/v1/notarius/minutas/{minuta_id}/approve/"
        )
        approval_time = time.time() - start_time
        
        assert approve_response.status_code == 200
        assert approval_time < 5.0, f"Approval too slow: {approval_time}s"
        
        # 3. Test finalization performance
        start_time = time.time()
        finalize_response = await self.notarius_client.post(
            f"/api/v1/notarius/minutas/{minuta_id}/finalize/"
        )
        finalization_time = time.time() - start_time
        
        assert finalize_response.status_code == 200
        assert finalization_time < 10.0, f"Finalization too slow: {finalization_time}s"
    
    @pytest.mark.asyncio
    async def test_notarius_concurrent_operations(self):
        """Test Notarius concurrent operations."""
        import asyncio
        
        # 1. Generate multiple minutas concurrently
        commands = [
            "Fazer procuração para João Silva, CPF 123.456.789-00",
            "Fazer contrato para Maria Santos, CPF 987.654.321-00",
            "Fazer testamento para Pedro Costa, CPF 111.222.333-44"
        ]
        
        async def generate_minuta(command):
            generate_payload = {
                "command": command,
                "processo_id": None
            }
            return await self.notarius_client.post(
                "/api/v1/notarius/ai/generate/",
                json=generate_payload
            )
        
        # Generate minutas concurrently
        tasks = [generate_minuta(command) for command in commands]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        minuta_ids = []
        for response in responses:
            assert response.status_code == 201
            data = response.json()
            minuta_ids.append(data["minuta_id"])
        
        # 2. Approve all minutas concurrently
        async def approve_minuta(minuta_id):
            return await self.notarius_client.post(
                f"/api/v1/notarius/minutas/{minuta_id}/approve/"
            )
        
        tasks = [approve_minuta(minuta_id) for minuta_id in minuta_ids]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
        
        # 3. Finalize all minutas concurrently
        async def finalize_minuta(minuta_id):
            return await self.notarius_client.post(
                f"/api/v1/notarius/minutas/{minuta_id}/finalize/"
            )
        
        tasks = [finalize_minuta(minuta_id) for minuta_id in minuta_ids]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_notarius_audit_logging(self):
        """Test Notarius audit logging."""
        # 1. Generate minuta
        command = "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel."
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json={"command": command, "processo_id": None}
        )
        
        assert generate_response.status_code == 201
        minuta_id = generate_response.json()["minuta_id"]
        
        # 2. Approve minuta
        approve_response = await self.notarius_client.post(
            f"/api/v1/notarius/minutas/{minuta_id}/approve/"
        )
        assert approve_response.status_code == 200
        
        # 3. Finalize minuta
        finalize_response = await self.notarius_client.post(
            f"/api/v1/notarius/minutas/{minuta_id}/finalize/"
        )
        assert finalize_response.status_code == 200
        
        # 4. Check audit logs
        audit_response = await self.notarius_client.get(
            f"/api/v1/notarius/audit/?resource_type=minuta&resource_id={minuta_id}"
        )
        assert audit_response.status_code == 200
        
        audit_data = audit_response.json()
        assert len(audit_data["results"]) >= 3  # create, approve, finalize
        
        # Verify audit log entries
        audit_entries = audit_data["results"]
        actions = [entry["action"] for entry in audit_entries]
        assert "create" in actions
        assert "approve" in actions
        assert "finalize" in actions
    
    @pytest.mark.asyncio
    async def test_notarius_processo_management(self):
        """Test Notarius processo management."""
        # 1. Create processo
        processo_payload = {
            "tipo_ato": "procuração",
            "numero": "TEST-2024-001",
            "descricao": "Processo de teste para AI workflow"
        }
        
        processo_response = await self.notarius_client.post(
            "/api/v1/notarius/processos/",
            json=processo_payload
        )
        
        assert processo_response.status_code == 201
        processo_data = processo_response.json()
        processo_id = processo_data["id"]
        
        # 2. Generate minuta for existing processo
        command = "Fazer procuração para Maria Santos, CPF 987.654.321-00, outorgar poderes para comprar imóvel."
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json={"command": command, "processo_id": processo_id}
        )
        
        assert generate_response.status_code == 201
        generate_data = generate_response.json()
        minuta_id = generate_data["minuta_id"]
        
        # 3. Verify minuta is associated with correct processo
        minuta_response = await self.notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
        assert minuta_response.status_code == 200
        
        minuta_data = minuta_response.json()
        assert minuta_data["processo_id"] == processo_id
        
        # 4. Approve and finalize
        await self.notarius_client.post(f"/api/v1/notarius/minutas/{minuta_id}/approve/")
        finalize_response = await self.notarius_client.post(f"/api/v1/notarius/minutas/{minuta_id}/finalize/")
        
        assert finalize_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_notarius_minuta_workflow(self):
        """Test Notarius minuta workflow."""
        # 1. Generate minuta
        command = "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em SP."
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json={"command": command, "processo_id": None}
        )
        
        assert generate_response.status_code == 201
        generate_data = generate_response.json()
        
        minuta_id = generate_data["minuta_id"]
        assert minuta_id is not None
        assert generate_data["status"] == "rascunho"
        assert generate_data["confidence"] > 0.0
        assert generate_data["citations_count"] > 0
        
        # 2. Get minuta details
        minuta_response = await self.notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
        assert minuta_response.status_code == 200
        
        minuta_data = minuta_response.json()
        assert minuta_data["id"] == minuta_id
        assert minuta_data["status"] == "rascunho"
        assert minuta_data["corpo_md"] is not None
        assert len(minuta_data["citations"]) > 0
        assert minuta_data["grounding_confidence"] > 0.0
        
        # 3. Approve minuta
        approve_response = await self.notarius_client.post(
            f"/api/v1/notarius/minutas/{minuta_id}/approve/"
        )
        assert approve_response.status_code == 200
        
        approve_data = approve_response.json()
        assert approve_data["minuta_id"] == minuta_id
        assert approve_data["status"] == "aprovado"
        assert approve_data["approved_at"] is not None
        assert approve_data["approved_by"] is not None
        
        # 4. Finalize minuta
        finalize_response = await self.notarius_client.post(
            f"/api/v1/notarius/minutas/{minuta_id}/finalize/"
        )
        assert finalize_response.status_code == 200
        
        finalize_data = finalize_response.json()
        assert finalize_data["minuta_id"] == minuta_id
        assert finalize_data["status"] == "finalizado"
        assert finalize_data["documento_id"] is not None
        assert finalize_data["finalized_at"] is not None
        assert finalize_data["download_url"] is not None
        
        # 5. Download final document
        download_response = await self.notarius_client.get(finalize_data["download_url"])
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/pdf"
        assert len(download_response.content) > 0
    
    @pytest.mark.asyncio
    async def test_notarius_pii_protection(self):
        """Test Notarius PII protection."""
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
    async def test_notarius_validation(self):
        """Test Notarius validation."""
        # 1. Test with invalid command
        generate_payload = {
            "command": "",
            "processo_id": None
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        # Should return error
        assert generate_response.status_code >= 400
        
        # 2. Test with invalid processo_id
        generate_payload = {
            "command": "Fazer procuração para João Silva",
            "processo_id": "invalid-uuid"
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        # Should return error
        assert generate_response.status_code >= 400
        
        # 3. Test with non-existent processo_id
        generate_payload = {
            "command": "Fazer procuração para João Silva",
            "processo_id": "00000000-0000-0000-0000-000000000000"
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        # Should return error
        assert generate_response.status_code >= 400
    
    @pytest.mark.asyncio
    async def test_notarius_security(self):
        """Test Notarius security."""
        # 1. Test with malicious command
        malicious_command = "DROP TABLE users; Fazer procuração para João Silva"
        
        generate_payload = {
            "command": malicious_command,
            "processo_id": None
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        # Should handle malicious command gracefully
        assert generate_response.status_code in [200, 201, 400, 422]
        
        # 2. Test with invalid processo_id
        generate_payload = {
            "command": "Fazer procuração para João Silva",
            "processo_id": "invalid-uuid"
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        # Should handle invalid processo_id gracefully
        assert generate_response.status_code in [400, 422]
    
    @pytest.mark.asyncio
    async def test_notarius_large_dataset(self):
        """Test Notarius with large dataset."""
        # 1. Generate many minutas
        commands = [
            f"Fazer procuração para Pessoa {i}, CPF {i:011d}, outorgar poderes para vender imóvel."
            for i in range(100)
        ]
        
        minuta_ids = []
        for command in commands:
            generate_response = await self.notarius_client.post(
                "/api/v1/notarius/ai/generate/",
                json={"command": command, "processo_id": None}
            )
            
            assert generate_response.status_code == 201
            minuta_ids.append(generate_response.json()["minuta_id"])
        
        # 2. Approve all minutas
        for minuta_id in minuta_ids:
            approve_response = await self.notarius_client.post(
                f"/api/v1/notarius/minutas/{minuta_id}/approve/"
            )
            assert approve_response.status_code == 200
        
        # 3. Finalize all minutas
        for minuta_id in minuta_ids:
            finalize_response = await self.notarius_client.post(
                f"/api/v1/notarius/minutas/{minuta_id}/finalize/"
            )
            assert finalize_response.status_code == 200
        
        # 4. Verify all minutas are finalized
        for minuta_id in minuta_ids:
            minuta_response = await self.notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
            assert minuta_response.status_code == 200
            
            minuta_data = minuta_response.json()
            assert minuta_data["status"] == "finalizado"
            assert minuta_data["final_document_id"] is not None
