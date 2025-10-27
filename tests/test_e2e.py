"""
End-to-end tests for complete workflows.
"""
import pytest
import time
from unittest.mock import patch, MagicMock


class TestCompleteWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_complete_procuracao_workflow(self, notarius_client, lexnode_client, intent_engine_client, pii_vault_client, mock_services):
        """Test complete procuração workflow from intent to final document."""
        
        # Step 1: Parse intent
        intent_response = intent_engine_client.post("/api/v1/parse-intent", json={
            "intent": "Criar uma procuração para João Silva representar Maria Santos em uma compra e venda de imóvel",
            "processo_id": "proc_123",
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert intent_response.status_code == 200
        intent_data = intent_response.json()
        assert intent_data["parsed_intent"]["action"] == "create"
        assert intent_data["parsed_intent"]["document_type"] == "procuracao"
        
        # Step 2: Extract PII
        pii_response = intent_engine_client.post("/api/v1/extract-pii", json={
            "text": "João Silva, CPF 123.456.789-00, residente na Rua das Flores, 123",
            "extraction_types": ["nome", "cpf", "endereco"]
        })
        
        assert pii_response.status_code == 200
        pii_data = pii_response.json()
        assert "João Silva" in pii_data["extracted_pii"]["nome"]
        assert "123.456.789-00" in pii_data["extracted_pii"]["cpf"]
        
        # Step 3: Store PII in vault
        vault_response = pii_vault_client.post("/api/v1/store-pii", json={
            "pii_data": pii_data["extracted_pii"],
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert vault_response.status_code == 200
        vault_data = vault_response.json()
        assert vault_data["status"] == "success"
        assert vault_data["pii_id"] is not None
        
        # Step 4: Tokenize PII
        tokenize_response = pii_vault_client.post("/api/v1/tokenize", json={
            "pii_data": pii_data["extracted_pii"],
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert tokenize_response.status_code == 200
        tokenize_data = tokenize_response.json()
        assert tokenize_data["status"] == "success"
        assert "TOKEN_NOME" in tokenize_data["tokens"]["nome"]
        assert "TOKEN_CPF" in tokenize_data["tokens"]["cpf"]
        
        # Step 5: Get legal citations
        citations_response = intent_engine_client.post("/api/v1/legal-citations", json={
            "intent": "Criar uma procuração para João Silva representar Maria Santos em uma compra e venda de imóvel",
            "jurisdiction": "RJ"
        })
        
        assert citations_response.status_code == 200
        citations_data = citations_response.json()
        assert citations_data["total"] > 0
        assert len(citations_data["citations"]) > 0
        
        # Step 6: Generate draft
        draft_response = intent_engine_client.post("/api/v1/generate-draft", json={
            "intent_id": intent_data["intent_id"],
            "template_id": "template_456",
            "processo_id": "proc_123",
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert draft_response.status_code == 200
        draft_data = draft_response.json()
        assert "PROCURAÇÃO" in draft_data["content"]
        assert draft_data["grounding_confidence"] > 0.8
        assert len(draft_data["citations"]) > 0
        
        # Step 7: Validate draft
        validation_response = intent_engine_client.post("/api/v1/validate-intent", json={
            "intent": "Criar uma procuração para João Silva representar Maria Santos em uma compra e venda de imóvel",
            "document_type": "procuracao"
        })
        
        assert validation_response.status_code == 200
        validation_data = validation_response.json()
        assert validation_data["is_valid"] is True
        assert validation_data["confidence"] > 0.8
        
        # Step 8: Finalize document (Notarius API)
        finalize_response = notarius_client.post("/api/v1/documentos/minutas/finalize/", json={
            "minuta_id": "minuta_123",
            "final_content": draft_data["content"],
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert finalize_response.status_code == 200
        finalize_data = finalize_response.json()
        assert finalize_data["status"] == "success"
        assert finalize_data["document_id"] is not None
    
    def test_complete_certidao_workflow(self, notarius_client, lexnode_client, intent_engine_client, pii_vault_client, mock_services):
        """Test complete certidão workflow from intent to final document."""
        
        # Step 1: Parse intent
        intent_response = intent_engine_client.post("/api/v1/parse-intent", json={
            "intent": "Criar uma certidão de nascimento para João Silva",
            "processo_id": "proc_456",
            "tenant_id": "tenant_789",
            "user_id": "user_101"
        })
        
        assert intent_response.status_code == 200
        intent_data = intent_response.json()
        assert intent_data["parsed_intent"]["action"] == "create"
        assert intent_data["parsed_intent"]["document_type"] == "certidao"
        
        # Step 2: Extract PII
        pii_response = intent_engine_client.post("/api/v1/extract-pii", json={
            "text": "João Silva, nascido em 01/01/1990, filho de Maria Silva e José Silva",
            "extraction_types": ["nome", "data_nascimento", "nome_pai", "nome_mae"]
        })
        
        assert pii_response.status_code == 200
        pii_data = pii_response.json()
        assert "João Silva" in pii_data["extracted_pii"]["nome"]
        assert "01/01/1990" in pii_data["extracted_pii"]["data_nascimento"]
        
        # Step 3: Store PII in vault
        vault_response = pii_vault_client.post("/api/v1/store-pii", json={
            "pii_data": pii_data["extracted_pii"],
            "tenant_id": "tenant_789",
            "user_id": "user_101"
        })
        
        assert vault_response.status_code == 200
        vault_data = vault_response.json()
        assert vault_data["status"] == "success"
        
        # Step 4: Get legal citations
        citations_response = intent_engine_client.post("/api/v1/legal-citations", json={
            "intent": "Criar uma certidão de nascimento para João Silva",
            "jurisdiction": "RJ"
        })
        
        assert citations_response.status_code == 200
        citations_data = citations_response.json()
        assert citations_data["total"] > 0
        
        # Step 5: Generate draft
        draft_response = intent_engine_client.post("/api/v1/generate-draft", json={
            "intent_id": intent_data["intent_id"],
            "template_id": "template_789",
            "processo_id": "proc_456",
            "tenant_id": "tenant_789",
            "user_id": "user_101"
        })
        
        assert draft_response.status_code == 200
        draft_data = draft_response.json()
        assert "CERTIDÃO" in draft_data["content"]
        assert draft_data["grounding_confidence"] > 0.8
        
        # Step 6: Finalize document
        finalize_response = notarius_client.post("/api/v1/documentos/minutas/finalize/", json={
            "minuta_id": "minuta_456",
            "final_content": draft_data["content"],
            "tenant_id": "tenant_789",
            "user_id": "user_101"
        })
        
        assert finalize_response.status_code == 200
        finalize_data = finalize_response.json()
        assert finalize_data["status"] == "success"
    
    def test_complete_testamento_workflow(self, notarius_client, lexnode_client, intent_engine_client, pii_vault_client, mock_services):
        """Test complete testamento workflow from intent to final document."""
        
        # Step 1: Parse intent
        intent_response = intent_engine_client.post("/api/v1/parse-intent", json={
            "intent": "Criar um testamento para João Silva deixar seus bens para Maria Santos",
            "processo_id": "proc_789",
            "tenant_id": "tenant_101",
            "user_id": "user_202"
        })
        
        assert intent_response.status_code == 200
        intent_data = intent_response.json()
        assert intent_data["parsed_intent"]["action"] == "create"
        assert intent_data["parsed_intent"]["document_type"] == "testamento"
        
        # Step 2: Extract PII
        pii_response = intent_engine_client.post("/api/v1/extract-pii", json={
            "text": "João Silva, CPF 123.456.789-00, deixa seus bens para Maria Santos, CPF 987.654.321-00",
            "extraction_types": ["nome", "cpf"]
        })
        
        assert pii_response.status_code == 200
        pii_data = pii_response.json()
        assert "João Silva" in pii_data["extracted_pii"]["nome"]
        assert "123.456.789-00" in pii_data["extracted_pii"]["cpf"]
        
        # Step 3: Store PII in vault
        vault_response = pii_vault_client.post("/api/v1/store-pii", json={
            "pii_data": pii_data["extracted_pii"],
            "tenant_id": "tenant_101",
            "user_id": "user_202"
        })
        
        assert vault_response.status_code == 200
        vault_data = vault_response.json()
        assert vault_data["status"] == "success"
        
        # Step 4: Get legal citations
        citations_response = intent_engine_client.post("/api/v1/legal-citations", json={
            "intent": "Criar um testamento para João Silva deixar seus bens para Maria Santos",
            "jurisdiction": "RJ"
        })
        
        assert citations_response.status_code == 200
        citations_data = citations_response.json()
        assert citations_data["total"] > 0
        
        # Step 5: Generate draft
        draft_response = intent_engine_client.post("/api/v1/generate-draft", json={
            "intent_id": intent_data["intent_id"],
            "template_id": "template_101",
            "processo_id": "proc_789",
            "tenant_id": "tenant_101",
            "user_id": "user_202"
        })
        
        assert draft_response.status_code == 200
        draft_data = draft_response.json()
        assert "TESTAMENTO" in draft_data["content"]
        assert draft_data["grounding_confidence"] > 0.8
        
        # Step 6: Finalize document
        finalize_response = notarius_client.post("/api/v1/documentos/minutas/finalize/", json={
            "minuta_id": "minuta_789",
            "final_content": draft_data["content"],
            "tenant_id": "tenant_101",
            "user_id": "user_202"
        })
        
        assert finalize_response.status_code == 200
        finalize_data = finalize_response.json()
        assert finalize_data["status"] == "success"


class TestErrorRecoveryWorkflow:
    """Test error recovery in end-to-end workflows."""
    
    def test_workflow_with_service_failure_recovery(self, notarius_client, lexnode_client, intent_engine_client, pii_vault_client, mock_services):
        """Test workflow recovery when a service fails and recovers."""
        
        # Step 1: Parse intent successfully
        intent_response = intent_engine_client.post("/api/v1/parse-intent", json={
            "intent": "Criar uma procuração para João Silva representar Maria Santos",
            "processo_id": "proc_123",
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert intent_response.status_code == 200
        intent_data = intent_response.json()
        
        # Step 2: Simulate PII service failure
        mock_services["pii"].return_value.extract_pii.side_effect = Exception("PII service temporarily unavailable")
        
        pii_response = intent_engine_client.post("/api/v1/extract-pii", json={
            "text": "João Silva, CPF 123.456.789-00",
            "extraction_types": ["nome", "cpf"]
        })
        
        assert pii_response.status_code == 500
        
        # Step 3: Simulate PII service recovery
        mock_services["pii"].return_value.extract_pii.side_effect = None
        mock_services["pii"].return_value.extract_pii.return_value = {
            "extracted_pii": {
                "nome": ["João Silva"],
                "cpf": ["123.456.789-00"]
            },
            "confidence": 0.95
        }
        
        pii_response = intent_engine_client.post("/api/v1/extract-pii", json={
            "text": "João Silva, CPF 123.456.789-00",
            "extraction_types": ["nome", "cpf"]
        })
        
        assert pii_response.status_code == 200
        pii_data = pii_response.json()
        assert "João Silva" in pii_data["extracted_pii"]["nome"]
        
        # Step 4: Continue workflow
        vault_response = pii_vault_client.post("/api/v1/store-pii", json={
            "pii_data": pii_data["extracted_pii"],
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert vault_response.status_code == 200
    
    def test_workflow_with_partial_failure(self, notarius_client, lexnode_client, intent_engine_client, pii_vault_client, mock_services):
        """Test workflow with partial failure and fallback mechanisms."""
        
        # Step 1: Parse intent successfully
        intent_response = intent_engine_client.post("/api/v1/parse-intent", json={
            "intent": "Criar uma procuração para João Silva representar Maria Santos",
            "processo_id": "proc_123",
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert intent_response.status_code == 200
        intent_data = intent_response.json()
        
        # Step 2: Simulate LexNode service failure
        mock_services["retrieval"].return_value.retrieve.side_effect = Exception("LexNode service unavailable")
        
        citations_response = intent_engine_client.post("/api/v1/legal-citations", json={
            "intent": "Criar uma procuração para João Silva representar Maria Santos",
            "jurisdiction": "RJ"
        })
        
        assert citations_response.status_code == 500
        
        # Step 3: Generate draft without citations (fallback)
        draft_response = intent_engine_client.post("/api/v1/generate-draft", json={
            "intent_id": intent_data["intent_id"],
            "template_id": "template_456",
            "processo_id": "proc_123",
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert draft_response.status_code == 200
        draft_data = draft_response.json()
        assert "PROCURAÇÃO" in draft_data["content"]
        # Should still generate draft even without citations
        assert draft_data["grounding_confidence"] > 0.5
    
    def test_workflow_with_timeout_recovery(self, notarius_client, lexnode_client, intent_engine_client, pii_vault_client, mock_services):
        """Test workflow recovery from timeout errors."""
        
        # Step 1: Parse intent successfully
        intent_response = intent_engine_client.post("/api/v1/parse-intent", json={
            "intent": "Criar uma procuração para João Silva representar Maria Santos",
            "processo_id": "proc_123",
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert intent_response.status_code == 200
        intent_data = intent_response.json()
        
        # Step 2: Simulate timeout
        mock_services["draft"].return_value.generate_draft.side_effect = TimeoutError("Service timeout")
        
        draft_response = intent_engine_client.post("/api/v1/generate-draft", json={
            "intent_id": intent_data["intent_id"],
            "template_id": "template_456",
            "processo_id": "proc_123",
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert draft_response.status_code == 504
        
        # Step 3: Simulate recovery
        mock_services["draft"].return_value.generate_draft.side_effect = None
        mock_services["draft"].return_value.generate_draft.return_value = {
            "draft_id": "draft_123",
            "content": "PROCURAÇÃO\n\nJoão Silva, CPF 123.456.789-00, nomeia Maria Santos como seu procurador...",
            "grounding_confidence": 0.92,
            "citations": []
        }
        
        draft_response = intent_engine_client.post("/api/v1/generate-draft", json={
            "intent_id": intent_data["intent_id"],
            "template_id": "template_456",
            "processo_id": "proc_123",
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert draft_response.status_code == 200
        draft_data = draft_response.json()
        assert "PROCURAÇÃO" in draft_data["content"]


class TestPerformanceWorkflow:
    """Test performance characteristics of end-to-end workflows."""
    
    def test_workflow_performance_under_load(self, notarius_client, lexnode_client, intent_engine_client, pii_vault_client, mock_services):
        """Test workflow performance under load."""
        
        start_time = time.time()
        
        # Execute multiple workflows concurrently
        responses = []
        for i in range(10):
            intent_response = intent_engine_client.post("/api/v1/parse-intent", json={
                "intent": f"Criar uma procuração para João Silva {i} representar Maria Santos {i}",
                "processo_id": f"proc_{i}",
                "tenant_id": "tenant_456",
                "user_id": "user_789"
            })
            responses.append(intent_response)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert execution_time < 30.0  # 30 seconds for 10 concurrent requests
    
    def test_workflow_memory_usage(self, notarius_client, lexnode_client, intent_engine_client, pii_vault_client, mock_services):
        """Test workflow memory usage."""
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Execute multiple workflows
        for i in range(100):
            intent_response = intent_engine_client.post("/api/v1/parse-intent", json={
                "intent": f"Criar uma procuração para João Silva {i} representar Maria Santos {i}",
                "processo_id": f"proc_{i}",
                "tenant_id": "tenant_456",
                "user_id": "user_789"
            })
            assert intent_response.status_code == 200
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (adjust threshold as needed)
        assert memory_increase < 100 * 1024 * 1024  # 100MB
    
    def test_workflow_concurrent_users(self, notarius_client, lexnode_client, intent_engine_client, pii_vault_client, mock_services):
        """Test workflow with concurrent users."""
        
        import threading
        import queue
        
        results = queue.Queue()
        
        def execute_workflow(user_id):
            try:
                intent_response = intent_engine_client.post("/api/v1/parse-intent", json={
                    "intent": f"Criar uma procuração para João Silva representar Maria Santos",
                    "processo_id": f"proc_{user_id}",
                    "tenant_id": "tenant_456",
                    "user_id": f"user_{user_id}"
                })
                results.put(("success", user_id, intent_response.status_code))
            except Exception as e:
                results.put(("error", user_id, str(e)))
        
        # Create multiple threads simulating concurrent users
        threads = []
        for i in range(20):
            thread = threading.Thread(target=execute_workflow, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        error_count = 0
        
        while not results.empty():
            result_type, user_id, result = results.get()
            if result_type == "success":
                success_count += 1
                assert result == 200
            else:
                error_count += 1
        
        # Most requests should succeed
        assert success_count > 15  # At least 15 out of 20 should succeed
        assert error_count < 5     # At most 5 should fail
