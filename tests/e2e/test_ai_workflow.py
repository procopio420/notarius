"""
End-to-end tests for AI workflow
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch


class TestAIWorkflowE2E:
    """Test complete AI workflow end-to-end."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.notarius_url = "http://localhost:8000"
        self.lexnode_url = "http://localhost:8001"
        self.pii_vault_url = "http://localhost:8002"
        self.intent_engine_url = "http://localhost:8003"
        
        self.notarius_client = httpx.AsyncClient(base_url=self.notarius_url)
        self.lexnode_client = httpx.AsyncClient(base_url=self.lexnode_url)
        self.pii_vault_client = httpx.AsyncClient(base_url=self.pii_vault_url)
        self.intent_engine_client = httpx.AsyncClient(base_url=self.intent_engine_url)
        
        self.tenant_id = "test-tenant-123"
        self.user_id = "test-user-456"
    
    @pytest.mark.asyncio
    async def test_complete_ai_workflow(self):
        """Test complete AI workflow from command to final document."""
        # 1. Generate minuta from natural language command
        command = "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em SP."
        
        generate_payload = {
            "command": command,
            "processo_id": None  # Let backend create new processo
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
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
    async def test_ai_workflow_with_existing_processo(self):
        """Test AI workflow with existing processo."""
        # 1. Create processo first
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
        
        generate_payload = {
            "command": command,
            "processo_id": processo_id
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        assert generate_response.status_code == 201
        generate_data = generate_response.json()
        
        minuta_id = generate_data["minuta_id"]
        assert minuta_id is not None
        
        # 3. Verify minuta is associated with correct processo
        minuta_response = await self.notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
        assert minuta_response.status_code == 200
        
        minuta_data = minuta_response.json()
        assert minuta_data["processo_id"] == processo_id
    
    @pytest.mark.asyncio
    async def test_ai_workflow_with_validation(self):
        """Test AI workflow with validation and confidence thresholds."""
        # 1. Generate minuta with validation
        command = "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel."
        
        generate_payload = {
            "command": command,
            "processo_id": None,
            "validate": True,
            "confidence_threshold": 0.8
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        assert generate_response.status_code == 201
        generate_data = generate_response.json()
        
        minuta_id = generate_data["minuta_id"]
        
        # 2. Verify minuta has high confidence
        minuta_response = await self.notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
        assert minuta_response.status_code == 200
        
        minuta_data = minuta_response.json()
        assert minuta_data["grounding_confidence"] >= 0.8
        
        # 3. Approve and finalize
        await self.notarius_client.post(f"/api/v1/notarius/minutas/{minuta_id}/approve/")
        finalize_response = await self.notarius_client.post(f"/api/v1/notarius/minutas/{minuta_id}/finalize/")
        
        assert finalize_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_ai_workflow_with_custom_patterns(self):
        """Test AI workflow with custom PII patterns."""
        # 1. Generate minuta with custom patterns
        command = "Fazer procuração para João Silva, ID: 123456, outorgar poderes para vender imóvel."
        
        generate_payload = {
            "command": command,
            "processo_id": None,
            "custom_patterns": {
                "custom_id": {
                    "pattern": r"\bID:\s*(\d{6})\b",
                    "type": "custom_id"
                }
            }
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        assert generate_response.status_code == 201
        generate_data = generate_response.json()
        
        minuta_id = generate_data["minuta_id"]
        
        # 2. Verify custom PII was extracted and tokenized
        minuta_response = await self.notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
        assert minuta_response.status_code == 200
        
        minuta_data = minuta_response.json()
        assert "custom_id" in minuta_data["variaveis_json"]
        
        # 3. Approve and finalize
        await self.notarius_client.post(f"/api/v1/notarius/minutas/{minuta_id}/approve/")
        finalize_response = await self.notarius_client.post(f"/api/v1/notarius/minutas/{minuta_id}/finalize/")
        
        assert finalize_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_ai_workflow_with_audit_logging(self):
        """Test AI workflow with audit logging."""
        # 1. Generate minuta
        command = "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel."
        
        generate_payload = {
            "command": command,
            "processo_id": None
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        assert generate_response.status_code == 201
        generate_data = generate_response.json()
        minuta_id = generate_data["minuta_id"]
        
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
    async def test_ai_workflow_with_error_handling(self):
        """Test AI workflow with error handling."""
        # 1. Test with invalid command
        invalid_command = ""
        
        generate_payload = {
            "command": invalid_command,
            "processo_id": None
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        assert generate_response.status_code == 400
        
        # 2. Test with invalid processo_id
        command = "Fazer procuração para João Silva"
        
        generate_payload = {
            "command": command,
            "processo_id": "invalid-uuid"
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        assert generate_response.status_code == 400
        
        # 3. Test with non-existent processo_id
        generate_payload = {
            "command": command,
            "processo_id": "00000000-0000-0000-0000-000000000000"
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        assert generate_response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_ai_workflow_with_concurrent_operations(self):
        """Test AI workflow with concurrent operations."""
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
    async def test_ai_workflow_with_performance_monitoring(self):
        """Test AI workflow with performance monitoring."""
        import time
        
        # 1. Monitor generation performance
        command = "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel."
        
        start_time = time.time()
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json={"command": command, "processo_id": None}
        )
        generation_time = time.time() - start_time
        
        assert generate_response.status_code == 201
        assert generation_time < 30.0, f"Generation too slow: {generation_time}s"
        
        # 2. Monitor approval performance
        minuta_id = generate_response.json()["minuta_id"]
        
        start_time = time.time()
        approve_response = await self.notarius_client.post(
            f"/api/v1/notarius/minutas/{minuta_id}/approve/"
        )
        approval_time = time.time() - start_time
        
        assert approve_response.status_code == 200
        assert approval_time < 5.0, f"Approval too slow: {approval_time}s"
        
        # 3. Monitor finalization performance
        start_time = time.time()
        finalize_response = await self.notarius_client.post(
            f"/api/v1/notarius/minutas/{minuta_id}/finalize/"
        )
        finalization_time = time.time() - start_time
        
        assert finalize_response.status_code == 200
        assert finalization_time < 10.0, f"Finalization too slow: {finalization_time}s"
    
    @pytest.mark.asyncio
    async def test_ai_workflow_with_metrics_collection(self):
        """Test AI workflow with metrics collection."""
        # 1. Generate minuta
        command = "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel."
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json={"command": command, "processo_id": None}
        )
        
        assert generate_response.status_code == 201
        minuta_id = generate_response.json()["minuta_id"]
        
        # 2. Approve and finalize
        await self.notarius_client.post(f"/api/v1/notarius/minutas/{minuta_id}/approve/")
        await self.notarius_client.post(f"/api/v1/notarius/minutas/{minuta_id}/finalize/")
        
        # 3. Check metrics
        metrics_response = await self.notarius_client.get("/metrics")
        assert metrics_response.status_code == 200
        
        metrics_content = metrics_response.text
        assert "http_requests_total" in metrics_content
        assert "ai_draft_generation_duration_seconds" in metrics_content
        assert "pii_vault_tokenize_duration_seconds" in metrics_content
        assert "lexnode_retrieval_duration_seconds" in metrics_content
    
    @pytest.mark.asyncio
    async def test_ai_workflow_with_large_dataset(self):
        """Test AI workflow with large dataset."""
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
    
    @pytest.mark.asyncio
    async def test_ai_workflow_with_validation_and_confidence(self):
        """Test AI workflow with validation and confidence thresholds."""
        # 1. Generate minuta with validation and confidence threshold
        command = "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel."
        
        generate_payload = {
            "command": command,
            "processo_id": None,
            "validate": True,
            "confidence_threshold": 0.9
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        assert generate_response.status_code == 201
        generate_data = generate_response.json()
        
        minuta_id = generate_data["minuta_id"]
        
        # 2. Verify minuta has high confidence
        minuta_response = await self.notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
        assert minuta_response.status_code == 200
        
        minuta_data = minuta_response.json()
        assert minuta_data["grounding_confidence"] >= 0.9
        
        # 3. Approve and finalize
        await self.notarius_client.post(f"/api/v1/notarius/minutas/{minuta_id}/approve/")
        finalize_response = await self.notarius_client.post(f"/api/v1/notarius/minutas/{minuta_id}/finalize/")
        
        assert finalize_response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_ai_workflow_with_custom_options(self):
        """Test AI workflow with custom options."""
        # 1. Generate minuta with custom options
        command = "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel."
        
        generate_payload = {
            "command": command,
            "processo_id": None,
            "custom_options": {
                "preserve_case": True,
                "preserve_punctuation": True,
                "use_ner": True
            }
        }
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json=generate_payload
        )
        
        assert generate_response.status_code == 201
        generate_data = generate_response.json()
        
        minuta_id = generate_data["minuta_id"]
        
        # 2. Verify minuta was generated with custom options
        minuta_response = await self.notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
        assert minuta_response.status_code == 200
        
        minuta_data = minuta_response.json()
        assert minuta_data["corpo_md"] is not None
        
        # 3. Approve and finalize
        await self.notarius_client.post(f"/api/v1/notarius/minutas/{minuta_id}/approve/")
        finalize_response = await self.notarius_client.post(f"/api/v1/notarius/minutas/{minuta_id}/finalize/")
        
        assert finalize_response.status_code == 200
