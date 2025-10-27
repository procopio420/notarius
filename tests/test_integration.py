"""
Integration tests for cross-service communication.
"""
import pytest
import time
from unittest.mock import patch, MagicMock


class TestNotariusLexNodeIntegration:
    """Test integration between Notarius and LexNode services."""
    
    def test_notarius_calls_lexnode_for_legal_citations(self, notarius_client, lexnode_client, mock_services):
        """Test that Notarius calls LexNode for legal citations."""
        # Mock LexNode response
        mock_services["retrieval"].return_value.retrieve.return_value = {
            "status": "success",
            "results": [
                {
                    "id": "doc_1",
                    "title": "Lei 8.935/1994",
                    "content": "Art. 1º - A procuração é o instrumento...",
                    "relevance_score": 0.95
                }
            ]
        }
        
        # Test LexNode endpoint directly
        response = lexnode_client.post("/api/v1/retrieve", json={
            "query": "procuração",
            "jurisdiction": "RJ",
            "limit": 10
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "Lei 8.935/1994"
    
    def test_notarius_calls_lexnode_for_document_processing(self, notarius_client, lexnode_client, mock_services):
        """Test that Notarius calls LexNode for document processing."""
        # Mock LexNode response
        mock_services["crawler"].return_value.crawl.return_value = {
            "status": "success",
            "documents": [
                {
                    "id": "doc_1",
                    "title": "Lei 8.935/1994",
                    "content": "Art. 1º - A procuração é o instrumento...",
                    "url": "https://example.com/lei-8935-1994"
                }
            ]
        }
        
        # Test LexNode endpoint directly
        response = lexnode_client.post("/api/v1/crawl", json={
            "urls": ["https://example.com/lei-8935-1994"],
            "jurisdiction": "RJ"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["documents"]) == 1
        assert data["documents"][0]["title"] == "Lei 8.935/1994"
    
    def test_notarius_calls_lexnode_for_indexing(self, notarius_client, lexnode_client, mock_services):
        """Test that Notarius calls LexNode for document indexing."""
        # Mock LexNode response
        mock_services["indexer"].return_value.index.return_value = {
            "status": "success",
            "indexed_count": 1
        }
        
        # Test LexNode endpoint directly
        response = lexnode_client.post("/api/v1/index", json={
            "documents": [
                {
                    "id": "doc_1",
                    "title": "Lei 8.935/1994",
                    "content": "Art. 1º - A procuração é o instrumento...",
                    "metadata": {
                        "source": "Lei 8.935/1994",
                        "article": "1",
                        "type": "law"
                    }
                }
            ],
            "jurisdiction": "RJ"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["indexed_count"] == 1


class TestNotariusIntentEngineIntegration:
    """Test integration between Notarius and Intent Engine services."""
    
    def test_notarius_calls_intent_engine_for_intent_parsing(self, notarius_client, intent_engine_client, mock_services):
        """Test that Notarius calls Intent Engine for intent parsing."""
        # Mock Intent Engine response
        mock_services["intent"].return_value.parse_intent.return_value = {
            "intent_id": "intent_123",
            "parsed_intent": {
                "action": "create",
                "document_type": "procuracao",
                "entities": {
                    "outorgante": "João Silva",
                    "outorgado": "Maria Santos"
                }
            },
            "confidence": 0.92
        }
        
        # Test Intent Engine endpoint directly
        response = intent_engine_client.post("/api/v1/parse-intent", json={
            "intent": "Criar uma procuração para João Silva representar Maria Santos",
            "processo_id": "proc_123",
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent_id"] == "intent_123"
        assert data["parsed_intent"]["action"] == "create"
        assert data["parsed_intent"]["document_type"] == "procuracao"
        assert data["confidence"] == 0.92
    
    def test_notarius_calls_intent_engine_for_draft_generation(self, notarius_client, intent_engine_client, mock_services):
        """Test that Notarius calls Intent Engine for draft generation."""
        # Mock Intent Engine response
        mock_services["draft"].return_value.generate_draft.return_value = {
            "draft_id": "draft_123",
            "content": "PROCURAÇÃO\n\nJoão Silva, CPF 123.456.789-00, nomeia Maria Santos como seu procurador...",
            "grounding_confidence": 0.92,
            "citations": [
                {
                    "source": "Lei 8.935/1994",
                    "relevance": 0.95,
                    "excerpt": "Art. 1º - A procuração é o instrumento..."
                }
            ]
        }
        
        # Test Intent Engine endpoint directly
        response = intent_engine_client.post("/api/v1/generate-draft", json={
            "intent_id": "intent_123",
            "template_id": "template_456",
            "processo_id": "proc_789",
            "tenant_id": "tenant_101",
            "user_id": "user_202"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["draft_id"] == "draft_123"
        assert "PROCURAÇÃO" in data["content"]
        assert data["grounding_confidence"] == 0.92
        assert len(data["citations"]) == 1
    
    def test_notarius_calls_intent_engine_for_pii_extraction(self, notarius_client, intent_engine_client, mock_services):
        """Test that Notarius calls Intent Engine for PII extraction."""
        # Mock Intent Engine response
        mock_services["pii"].return_value.extract_pii.return_value = {
            "extracted_pii": {
                "nome": ["João Silva"],
                "cpf": ["123.456.789-00"]
            },
            "confidence": 0.95
        }
        
        # Test Intent Engine endpoint directly
        response = intent_engine_client.post("/api/v1/extract-pii", json={
            "text": "João Silva, CPF 123.456.789-00, residente no Rio de Janeiro",
            "extraction_types": ["nome", "cpf"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "João Silva" in data["extracted_pii"]["nome"]
        assert "123.456.789-00" in data["extracted_pii"]["cpf"]
        assert data["confidence"] == 0.95


class TestNotariusPIIVaultIntegration:
    """Test integration between Notarius and PII Vault services."""
    
    def test_notarius_calls_pii_vault_for_pii_storage(self, notarius_client, pii_vault_client, mock_services):
        """Test that Notarius calls PII Vault for PII storage."""
        # Mock PII Vault response
        mock_services["vault"].return_value.store_pii.return_value = {
            "status": "success",
            "pii_id": "pii_123"
        }
        
        # Test PII Vault endpoint directly
        response = pii_vault_client.post("/api/v1/store-pii", json={
            "pii_data": {
                "nome": "João Silva",
                "cpf": "123.456.789-00"
            },
            "tenant_id": "tenant_123",
            "user_id": "user_456"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["pii_id"] == "pii_123"
    
    def test_notarius_calls_pii_vault_for_pii_retrieval(self, notarius_client, pii_vault_client, mock_services):
        """Test that Notarius calls PII Vault for PII retrieval."""
        # Mock PII Vault response
        mock_services["vault"].return_value.retrieve_pii.return_value = {
            "status": "success",
            "pii_data": {
                "nome": "João Silva",
                "cpf": "123.456.789-00"
            }
        }
        
        # Test PII Vault endpoint directly
        response = pii_vault_client.get("/api/v1/retrieve-pii/pii_123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["pii_data"]["nome"] == "João Silva"
        assert data["pii_data"]["cpf"] == "123.456.789-00"
    
    def test_notarius_calls_pii_vault_for_tokenization(self, notarius_client, pii_vault_client, mock_services):
        """Test that Notarius calls PII Vault for tokenization."""
        # Mock PII Vault response
        mock_services["tokenizer"].return_value.tokenize.return_value = {
            "status": "success",
            "tokens": {
                "nome": "TOKEN_NOME_123",
                "cpf": "TOKEN_CPF_456"
            }
        }
        
        # Test PII Vault endpoint directly
        response = pii_vault_client.post("/api/v1/tokenize", json={
            "pii_data": {
                "nome": "João Silva",
                "cpf": "123.456.789-00"
            },
            "tenant_id": "tenant_123",
            "user_id": "user_456"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["tokens"]["nome"] == "TOKEN_NOME_123"
        assert data["tokens"]["cpf"] == "TOKEN_CPF_456"


class TestServiceErrorHandling:
    """Test error handling in cross-service communication."""
    
    def test_lexnode_service_unavailable(self, notarius_client, lexnode_client, mock_services):
        """Test handling when LexNode service is unavailable."""
        # Mock LexNode service error
        mock_services["retrieval"].return_value.retrieve.side_effect = Exception("Service unavailable")
        
        # Test LexNode endpoint with error
        response = lexnode_client.post("/api/v1/retrieve", json={
            "query": "procuração",
            "jurisdiction": "RJ",
            "limit": 10
        })
        
        assert response.status_code == 500
    
    def test_intent_engine_service_unavailable(self, notarius_client, intent_engine_client, mock_services):
        """Test handling when Intent Engine service is unavailable."""
        # Mock Intent Engine service error
        mock_services["intent"].return_value.parse_intent.side_effect = Exception("Service unavailable")
        
        # Test Intent Engine endpoint with error
        response = intent_engine_client.post("/api/v1/parse-intent", json={
            "intent": "Criar uma procuração para João Silva representar Maria Santos",
            "processo_id": "proc_123",
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert response.status_code == 500
    
    def test_pii_vault_service_unavailable(self, notarius_client, pii_vault_client, mock_services):
        """Test handling when PII Vault service is unavailable."""
        # Mock PII Vault service error
        mock_services["vault"].return_value.store_pii.side_effect = Exception("Service unavailable")
        
        # Test PII Vault endpoint with error
        response = pii_vault_client.post("/api/v1/store-pii", json={
            "pii_data": {
                "nome": "João Silva",
                "cpf": "123.456.789-00"
            },
            "tenant_id": "tenant_123",
            "user_id": "user_456"
        })
        
        assert response.status_code == 500


class TestServiceTimeoutHandling:
    """Test timeout handling in cross-service communication."""
    
    def test_lexnode_service_timeout(self, notarius_client, lexnode_client, mock_services):
        """Test handling when LexNode service times out."""
        # Mock LexNode service timeout
        mock_services["retrieval"].return_value.retrieve.side_effect = TimeoutError("Service timeout")
        
        # Test LexNode endpoint with timeout
        response = lexnode_client.post("/api/v1/retrieve", json={
            "query": "procuração",
            "jurisdiction": "RJ",
            "limit": 10
        })
        
        assert response.status_code == 504  # Gateway timeout
    
    def test_intent_engine_service_timeout(self, notarius_client, intent_engine_client, mock_services):
        """Test handling when Intent Engine service times out."""
        # Mock Intent Engine service timeout
        mock_services["intent"].return_value.parse_intent.side_effect = TimeoutError("Service timeout")
        
        # Test Intent Engine endpoint with timeout
        response = intent_engine_client.post("/api/v1/parse-intent", json={
            "intent": "Criar uma procuração para João Silva representar Maria Santos",
            "processo_id": "proc_123",
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        assert response.status_code == 504  # Gateway timeout
    
    def test_pii_vault_service_timeout(self, notarius_client, pii_vault_client, mock_services):
        """Test handling when PII Vault service times out."""
        # Mock PII Vault service timeout
        mock_services["vault"].return_value.store_pii.side_effect = TimeoutError("Service timeout")
        
        # Test PII Vault endpoint with timeout
        response = pii_vault_client.post("/api/v1/store-pii", json={
            "pii_data": {
                "nome": "João Silva",
                "cpf": "123.456.789-00"
            },
            "tenant_id": "tenant_123",
            "user_id": "user_456"
        })
        
        assert response.status_code == 504  # Gateway timeout


class TestServiceCircuitBreaker:
    """Test circuit breaker pattern in cross-service communication."""
    
    def test_lexnode_circuit_breaker(self, notarius_client, lexnode_client, mock_services):
        """Test circuit breaker for LexNode service."""
        # Mock multiple failures
        mock_services["retrieval"].return_value.retrieve.side_effect = Exception("Service error")
        
        # Make multiple requests to trigger circuit breaker
        for i in range(5):
            response = lexnode_client.post("/api/v1/retrieve", json={
                "query": "procuração",
                "jurisdiction": "RJ",
                "limit": 10
            })
            assert response.status_code == 500
        
        # Circuit breaker should be open now
        response = lexnode_client.post("/api/v1/retrieve", json={
            "query": "procuração",
            "jurisdiction": "RJ",
            "limit": 10
        })
        
        # Should return circuit breaker error
        assert response.status_code == 503
    
    def test_intent_engine_circuit_breaker(self, notarius_client, intent_engine_client, mock_services):
        """Test circuit breaker for Intent Engine service."""
        # Mock multiple failures
        mock_services["intent"].return_value.parse_intent.side_effect = Exception("Service error")
        
        # Make multiple requests to trigger circuit breaker
        for i in range(5):
            response = intent_engine_client.post("/api/v1/parse-intent", json={
                "intent": "Criar uma procuração para João Silva representar Maria Santos",
                "processo_id": "proc_123",
                "tenant_id": "tenant_456",
                "user_id": "user_789"
            })
            assert response.status_code == 500
        
        # Circuit breaker should be open now
        response = intent_engine_client.post("/api/v1/parse-intent", json={
            "intent": "Criar uma procuração para João Silva representar Maria Santos",
            "processo_id": "proc_123",
            "tenant_id": "tenant_456",
            "user_id": "user_789"
        })
        
        # Should return circuit breaker error
        assert response.status_code == 503
    
    def test_pii_vault_circuit_breaker(self, notarius_client, pii_vault_client, mock_services):
        """Test circuit breaker for PII Vault service."""
        # Mock multiple failures
        mock_services["vault"].return_value.store_pii.side_effect = Exception("Service error")
        
        # Make multiple requests to trigger circuit breaker
        for i in range(5):
            response = pii_vault_client.post("/api/v1/store-pii", json={
                "pii_data": {
                    "nome": "João Silva",
                    "cpf": "123.456.789-00"
                },
                "tenant_id": "tenant_123",
                "user_id": "user_456"
            })
            assert response.status_code == 500
        
        # Circuit breaker should be open now
        response = pii_vault_client.post("/api/v1/store-pii", json={
            "pii_data": {
                "nome": "João Silva",
                "cpf": "123.456.789-00"
            },
            "tenant_id": "tenant_123",
            "user_id": "user_456"
        })
        
        # Should return circuit breaker error
        assert response.status_code == 503
