"""
Tests for Intent Engine API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app


class TestIntentEngineAPI:
    """Test cases for Intent Engine API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "intent-engine"}
    
    def test_parse_intent(self, client, mock_intent_request, mock_intent_response):
        """Test intent parsing endpoint."""
        with patch('app.services.intent_service.IntentService.parse_intent') as mock_parse:
            mock_parse.return_value = mock_intent_response
            
            response = client.post("/api/v1/parse-intent", json=mock_intent_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["intent_id"] == "intent_123"
            assert data["parsed_intent"]["action"] == "create"
            assert data["parsed_intent"]["document_type"] == "procuracao"
            assert data["confidence"] == 0.92
    
    def test_parse_intent_invalid_request(self, client):
        """Test intent parsing with invalid request."""
        invalid_request = {
            "intent": "",  # Empty intent
            "processo_id": "proc_123"
        }
        
        response = client.post("/api/v1/parse-intent", json=invalid_request)
        assert response.status_code == 400
    
    def test_parse_intent_missing_fields(self, client):
        """Test intent parsing with missing required fields."""
        response = client.post("/api/v1/parse-intent", json={})
        assert response.status_code == 422  # Validation error
    
    def test_generate_draft(self, client, mock_draft_request, mock_draft_response):
        """Test draft generation endpoint."""
        with patch('app.services.draft_service.DraftService.generate_draft') as mock_generate:
            mock_generate.return_value = mock_draft_response
            
            response = client.post("/api/v1/generate-draft", json=mock_draft_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["draft_id"] == "draft_123"
            assert "PROCURAÇÃO" in data["content"]
            assert data["grounding_confidence"] == 0.92
    
    def test_generate_draft_invalid_request(self, client):
        """Test draft generation with invalid request."""
        invalid_request = {
            "intent_id": "",  # Empty intent_id
            "template_id": "template_456"
        }
        
        response = client.post("/api/v1/generate-draft", json=invalid_request)
        assert response.status_code == 400
    
    def test_extract_pii(self, client, mock_pii_extraction_request, mock_pii_extraction_response):
        """Test PII extraction endpoint."""
        with patch('app.services.pii_service.PIIService.extract_pii') as mock_extract:
            mock_extract.return_value = mock_pii_extraction_response
            
            response = client.post("/api/v1/extract-pii", json=mock_pii_extraction_request)
            
            assert response.status_code == 200
            data = response.json()
            assert "João Silva" in data["extracted_pii"]["nome"]
            assert "123.456.789-00" in data["extracted_pii"]["cpf"]
            assert data["confidence"] == 0.95
    
    def test_extract_pii_empty_text(self, client):
        """Test PII extraction with empty text."""
        request = {
            "text": "",
            "extraction_types": ["nome", "cpf"]
        }
        
        response = client.post("/api/v1/extract-pii", json=request)
        assert response.status_code == 400
    
    def test_get_legal_citations(self, client, mock_legal_citation_request, mock_legal_citation_response):
        """Test legal citation retrieval endpoint."""
        with patch('app.services.legal_service.LegalService.get_citations') as mock_citations:
            mock_citations.return_value = mock_legal_citation_response
            
            response = client.post("/api/v1/legal-citations", json=mock_legal_citation_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert len(data["citations"]) == 2
            assert data["citations"][0]["source"] == "Lei 8.935/1994"
    
    def test_get_legal_citations_invalid_request(self, client):
        """Test legal citation retrieval with invalid request."""
        invalid_request = {
            "intent": "",  # Empty intent
            "jurisdiction": "RJ"
        }
        
        response = client.post("/api/v1/legal-citations", json=invalid_request)
        assert response.status_code == 400
    
    def test_validate_intent(self, client):
        """Test intent validation endpoint."""
        request = {
            "intent": "Criar uma procuração para João Silva representar Maria Santos",
            "document_type": "procuracao"
        }
        
        with patch('app.services.intent_service.IntentService.validate_intent') as mock_validate:
            mock_validate.return_value = {
                "is_valid": True,
                "confidence": 0.95,
                "suggestions": [],
                "errors": []
            }
            
            response = client.post("/api/v1/validate-intent", json=request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is True
            assert data["confidence"] == 0.95
    
    def test_validate_intent_invalid(self, client):
        """Test intent validation with invalid intent."""
        request = {
            "intent": "Invalid intent that doesn't make sense",
            "document_type": "procuracao"
        }
        
        with patch('app.services.intent_service.IntentService.validate_intent') as mock_validate:
            mock_validate.return_value = {
                "is_valid": False,
                "confidence": 0.2,
                "suggestions": ["Consider specifying the document type"],
                "errors": ["Intent is too vague"]
            }
            
            response = client.post("/api/v1/validate-intent", json=request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_valid"] is False
            assert data["confidence"] == 0.2
            assert len(data["errors"]) > 0
    
    def test_get_supported_document_types(self, client):
        """Test get supported document types endpoint."""
        with patch('app.services.intent_service.IntentService.get_supported_document_types') as mock_types:
            mock_types.return_value = {
                "document_types": [
                    {
                        "type": "procuracao",
                        "name": "Procuração",
                        "description": "Documento de procuração",
                        "supported_actions": ["create", "modify", "revoke"]
                    },
                    {
                        "type": "certidao",
                        "name": "Certidão",
                        "description": "Documento de certidão",
                        "supported_actions": ["create", "modify"]
                    }
                ]
            }
            
            response = client.get("/api/v1/document-types")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["document_types"]) == 2
            assert data["document_types"][0]["type"] == "procuracao"
    
    def test_get_intent_templates(self, client):
        """Test get intent templates endpoint."""
        with patch('app.services.intent_service.IntentService.get_intent_templates') as mock_templates:
            mock_templates.return_value = {
                "templates": [
                    {
                        "id": "template_1",
                        "name": "Procuração Básica",
                        "description": "Template para procuração básica",
                        "example": "Criar uma procuração para [nome] representar [nome] em [assunto]",
                        "document_type": "procuracao"
                    }
                ]
            }
            
            response = client.get("/api/v1/intent-templates")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["templates"]) == 1
            assert data["templates"][0]["document_type"] == "procuracao"
    
    def test_parse_intent_with_special_characters(self, client, mock_intent_response):
        """Test intent parsing with special characters."""
        with patch('app.services.intent_service.IntentService.parse_intent') as mock_parse:
            mock_parse.return_value = mock_intent_response
            
            request = {
                "intent": "Criar uma procuração para João Silva (CPF: 123.456.789-00) representar Maria Santos em uma compra e venda de imóvel no valor de R$ 500.000,00",
                "processo_id": "proc_123",
                "tenant_id": "tenant_456",
                "user_id": "user_789"
            }
            
            response = client.post("/api/v1/parse-intent", json=request)
            
            assert response.status_code == 200
    
    def test_parse_intent_with_unicode(self, client, mock_intent_response):
        """Test intent parsing with unicode characters."""
        with patch('app.services.intent_service.IntentService.parse_intent') as mock_parse:
            mock_parse.return_value = mock_intent_response
            
            request = {
                "intent": "Criar uma procuração para João Silva representar Maria Santos em uma compra e venda de imóvel com acentos: ção, ñ, ü",
                "processo_id": "proc_123",
                "tenant_id": "tenant_456",
                "user_id": "user_789"
            }
            
            response = client.post("/api/v1/parse-intent", json=request)
            
            assert response.status_code == 200
    
    def test_parse_intent_sql_injection(self, client, mock_intent_response):
        """Test intent parsing with SQL injection attempts."""
        with patch('app.services.intent_service.IntentService.parse_intent') as mock_parse:
            mock_parse.return_value = mock_intent_response
            
            request = {
                "intent": "'; DROP TABLE intents; --",
                "processo_id": "proc_123",
                "tenant_id": "tenant_456",
                "user_id": "user_789"
            }
            
            response = client.post("/api/v1/parse-intent", json=request)
            
            # Should not cause SQL injection
            assert response.status_code == 200
    
    def test_parse_intent_xss_attempt(self, client, mock_intent_response):
        """Test intent parsing with XSS attempts."""
        with patch('app.services.intent_service.IntentService.parse_intent') as mock_parse:
            mock_parse.return_value = mock_intent_response
            
            request = {
                "intent": "<script>alert('XSS')</script>",
                "processo_id": "proc_123",
                "tenant_id": "tenant_456",
                "user_id": "user_789"
            }
            
            response = client.post("/api/v1/parse-intent", json=request)
            
            # Should not cause XSS
            assert response.status_code == 200
    
    def test_concurrent_requests(self, client, mock_intent_response):
        """Test concurrent intent parsing requests."""
        with patch('app.services.intent_service.IntentService.parse_intent') as mock_parse:
            mock_parse.return_value = mock_intent_response
            
            request = {
                "intent": "Criar uma procuração para João Silva representar Maria Santos",
                "processo_id": "proc_123",
                "tenant_id": "tenant_456",
                "user_id": "user_789"
            }
            
            # Simulate concurrent requests
            responses = []
            for i in range(10):
                response = client.post("/api/v1/parse-intent", json=request)
                responses.append(response)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
    
    def test_error_handling(self, client):
        """Test error handling in API endpoints."""
        with patch('app.services.intent_service.IntentService.parse_intent') as mock_parse:
            mock_parse.side_effect = Exception("AI service unavailable")
            
            request = {
                "intent": "Criar uma procuração para João Silva representar Maria Santos",
                "processo_id": "proc_123",
                "tenant_id": "tenant_456",
                "user_id": "user_789"
            }
            
            response = client.post("/api/v1/parse-intent", json=request)
            
            assert response.status_code == 500
    
    def test_rate_limiting(self, client, mock_intent_response):
        """Test rate limiting on intent parsing endpoint."""
        with patch('app.services.intent_service.IntentService.parse_intent') as mock_parse:
            mock_parse.return_value = mock_intent_response
            
            request = {
                "intent": "Criar uma procuração para João Silva representar Maria Santos",
                "processo_id": "proc_123",
                "tenant_id": "tenant_456",
                "user_id": "user_789"
            }
            
            # Make many requests quickly
            for i in range(100):
                response = client.post("/api/v1/parse-intent", json=request)
                if response.status_code == 429:  # Rate limited
                    break
            
            # Should eventually hit rate limit
            assert response.status_code in [200, 429]
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v1/parse-intent")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
    
    def test_content_type_validation(self, client):
        """Test content type validation."""
        response = client.post("/api/v1/parse-intent", 
                             data="invalid json",
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422
    
    def test_missing_content_type(self, client):
        """Test missing content type header."""
        response = client.post("/api/v1/parse-intent", 
                             data='{"intent": "test"}')
        assert response.status_code == 422
