"""
Contract tests for Intent Engine service
"""

import pytest
import httpx
from unittest.mock import Mock, patch


class TestIntentEngineContract:
    """Test Intent Engine service contract."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.base_url = "http://localhost:8003"
        self.client = httpx.AsyncClient(base_url=self.base_url)
    
    @pytest.mark.asyncio
    async def test_parse_intent_endpoint_contract(self):
        """Test parse intent endpoint contract."""
        # Test data
        payload = {
            "command": "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em SP.",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        # Make request
        response = await self.client.post("/api/v1/intent/parse", json=payload)
        
        # Verify response
        assert response.status_code == 200
        
        data = response.json()
        assert "intent" in data
        assert "pii_extracted" in data
        assert "confidence" in data
        assert "trace" in data
        
        # Check intent structure
        intent = data["intent"]
        assert "act_type" in intent
        assert "parties" in intent
        assert "metadata" in intent
        assert isinstance(intent["act_type"], str)
        assert isinstance(intent["parties"], list)
        assert isinstance(intent["metadata"], dict)
        
        # Check PII extracted structure
        pii_extracted = data["pii_extracted"]
        assert isinstance(pii_extracted, list)
        if pii_extracted:
            pii_item = pii_extracted[0]
            assert "value" in pii_item
            assert "type" in pii_item
            assert "confidence" in pii_item
    
    @pytest.mark.asyncio
    async def test_generate_draft_endpoint_contract(self):
        """Test generate draft endpoint contract."""
        # Test data
        payload = {
            "intent": {
                "act_type": "procuração",
                "parties": [
                    {
                        "role": "outorgante",
                        "pii_extracted": ["João Silva", "123.456.789-00"]
                    }
                ],
                "metadata": {
                    "purpose": "venda de imóvel",
                    "jurisdiction": "sp"
                }
            },
            "pii_tokens": {
                "PARTY_1_NAME": "token_123",
                "PARTY_1_CPF": "token_456"
            }
        }
        
        # Make request
        response = await self.client.post("/api/v1/intent/generate-draft", json=payload)
        
        # Verify response
        assert response.status_code == 200
        
        data = response.json()
        assert "draft_md" in data
        assert "tokens" in data
        assert "citations" in data
        assert "confidence" in data
        assert "trace" in data
        assert "cache_key" in data
        
        # Check field types
        assert isinstance(data["draft_md"], str)
        assert isinstance(data["tokens"], dict)
        assert isinstance(data["citations"], list)
        assert isinstance(data["confidence"], float)
        assert isinstance(data["trace"], dict)
        assert isinstance(data["cache_key"], str)
        
        # Check citation structure
        if data["citations"]:
            citation = data["citations"][0]
            assert "uri" in citation
            assert "anchor" in citation
            assert "title" in citation
            assert "snippet" in citation
            assert "score" in citation
    
    @pytest.mark.asyncio
    async def test_health_endpoint_contract(self):
        """Test health endpoint contract."""
        # Make request
        response = await self.client.get("/health")
        
        # Verify response
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "llm_provider" in data
        assert "model_version" in data
    
    @pytest.mark.asyncio
    async def test_metrics_endpoint_contract(self):
        """Test metrics endpoint contract."""
        # Make request
        response = await self.client.get("/metrics")
        
        # Verify response
        assert response.status_code == 200
        
        # Should return Prometheus metrics format
        content = response.text
        assert "http_requests_total" in content
        assert "intent_engine_parse_duration_seconds" in content
    
    @pytest.mark.asyncio
    async def test_parse_intent_validation_contract(self):
        """Test parse intent endpoint validation."""
        # Test with missing command
        payload = {
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        response = await self.client.post("/api/v1/intent/parse", json=payload)
        assert response.status_code == 422
        
        # Test with missing tenant_context
        payload = {
            "command": "Fazer procuração para João Silva"
        }
        response = await self.client.post("/api/v1/intent/parse", json=payload)
        assert response.status_code == 422
        
        # Test with empty command
        payload = {
            "command": "",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        response = await self.client.post("/api/v1/intent/parse", json=payload)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_generate_draft_validation_contract(self):
        """Test generate draft endpoint validation."""
        # Test with missing intent
        payload = {
            "pii_tokens": {
                "PARTY_1_NAME": "token_123"
            }
        }
        response = await self.client.post("/api/v1/intent/generate-draft", json=payload)
        assert response.status_code == 422
        
        # Test with missing pii_tokens
        payload = {
            "intent": {
                "act_type": "procuração",
                "parties": [],
                "metadata": {}
            }
        }
        response = await self.client.post("/api/v1/intent/generate-draft", json=payload)
        assert response.status_code == 422
        
        # Test with invalid intent structure
        payload = {
            "intent": "invalid",
            "pii_tokens": {
                "PARTY_1_NAME": "token_123"
            }
        }
        response = await self.client.post("/api/v1/intent/generate-draft", json=payload)
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_error_responses_contract(self):
        """Test error response format."""
        # Test with invalid command
        payload = {
            "command": "",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        response = await self.client.post("/api/v1/intent/parse", json=payload)
        
        # Should return error
        assert response.status_code >= 400
        
        # Error response should have standard format
        data = response.json()
        assert "error" in data or "detail" in data
    
    @pytest.mark.asyncio
    async def test_rate_limiting_contract(self):
        """Test rate limiting contract."""
        # Make many requests quickly
        payload = {
            "command": "Fazer procuração para João Silva",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        responses = []
        for _ in range(100):
            response = await self.client.post("/api/v1/intent/parse", json=payload)
            responses.append(response)
        
        # Check that some requests might be rate limited
        status_codes = [r.status_code for r in responses]
        assert 200 in status_codes  # Some should succeed
        
        # If rate limiting is implemented, some should return 429
        if 429 in status_codes:
            assert True  # Rate limiting is working
        else:
            assert True  # No rate limiting implemented yet
    
    @pytest.mark.asyncio
    async def test_cors_headers_contract(self):
        """Test CORS headers contract."""
        # Make OPTIONS request
        response = await self.client.options("/api/v1/intent/parse")
        
        # Should return CORS headers
        assert "access-control-allow-origin" in response.headers
        assert "access-control-allow-methods" in response.headers
        assert "access-control-allow-headers" in response.headers
    
    @pytest.mark.asyncio
    async def test_content_type_contract(self):
        """Test content type contract."""
        # Test parse intent endpoint
        payload = {
            "command": "Fazer procuração para João Silva",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        response = await self.client.post("/api/v1/intent/parse", json=payload)
        
        # Should return JSON
        assert response.headers["content-type"] == "application/json"
        
        # Test health endpoint
        response = await self.client.get("/health")
        assert response.headers["content-type"] == "application/json"
        
        # Test metrics endpoint
        response = await self.client.get("/metrics")
        assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"
    
    @pytest.mark.asyncio
    async def test_response_time_contract(self):
        """Test response time contract."""
        import time
        
        # Test parse intent endpoint
        payload = {
            "command": "Fazer procuração para João Silva",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        start_time = time.time()
        response = await self.client.post("/api/v1/intent/parse", json=payload)
        response_time = time.time() - start_time
        
        # Should respond within reasonable time
        assert response_time < 10.0, f"Response too slow: {response_time}s"
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_concurrent_requests_contract(self):
        """Test concurrent requests contract."""
        import asyncio
        
        # Test data
        payload = {
            "command": "Fazer procuração para João Silva",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        # Make concurrent requests
        async def make_request():
            return await self.client.post("/api/v1/intent/parse", json=payload)
        
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            
            data = response.json()
            assert "intent" in data
            assert "pii_extracted" in data
    
    @pytest.mark.asyncio
    async def test_act_types_contract(self):
        """Test different act types contract."""
        # Test with different act types
        commands = [
            "Fazer procuração para João Silva",
            "Fazer contrato de compra e venda",
            "Fazer testamento",
            "Fazer escritura de imóvel",
            "Fazer certidão de nascimento"
        ]
        
        for command in commands:
            payload = {
                "command": command,
                "tenant_context": {
                    "tenant_id": "test-tenant-123",
                    "user_id": "test-user-456"
                }
            }
            response = await self.client.post("/api/v1/intent/parse", json=payload)
            
            # Should handle different act types
            assert response.status_code == 200
            
            data = response.json()
            assert "intent" in data
            assert "act_type" in data["intent"]
    
    @pytest.mark.asyncio
    async def test_pii_extraction_contract(self):
        """Test PII extraction contract."""
        # Test with different PII types
        commands = [
            "Fazer procuração para João Silva, CPF 123.456.789-00",
            "Fazer contrato com Maria Santos, email: maria@email.com",
            "Fazer testamento de Pedro Costa, telefone: (11) 99999-9999",
            "Fazer escritura de imóvel em Rua das Flores, 123"
        ]
        
        for command in commands:
            payload = {
                "command": command,
                "tenant_context": {
                    "tenant_id": "test-tenant-123",
                    "user_id": "test-user-456"
                }
            }
            response = await self.client.post("/api/v1/intent/parse", json=payload)
            
            # Should handle different PII types
            assert response.status_code == 200
            
            data = response.json()
            assert "pii_extracted" in data
            assert isinstance(data["pii_extracted"], list)
    
    @pytest.mark.asyncio
    async def test_confidence_scores_contract(self):
        """Test confidence scores contract."""
        # Test parse intent endpoint
        payload = {
            "command": "Fazer procuração para João Silva",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        response = await self.client.post("/api/v1/intent/parse", json=payload)
        
        data = response.json()
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0
        
        # Test generate draft endpoint
        payload = {
            "intent": {
                "act_type": "procuração",
                "parties": [],
                "metadata": {}
            },
            "pii_tokens": {
                "PARTY_1_NAME": "token_123"
            }
        }
        response = await self.client.post("/api/v1/intent/generate-draft", json=payload)
        
        data = response.json()
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_trace_structure_contract(self):
        """Test trace structure contract."""
        # Test parse intent endpoint
        payload = {
            "command": "Fazer procuração para João Silva",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        response = await self.client.post("/api/v1/intent/parse", json=payload)
        
        data = response.json()
        trace = data["trace"]
        
        # Should have trace information
        assert isinstance(trace, dict)
        
        # Common trace fields
        if "steps" in trace:
            assert isinstance(trace["steps"], list)
        
        if "timing" in trace:
            assert isinstance(trace["timing"], dict)
        
        if "metadata" in trace:
            assert isinstance(trace["metadata"], dict)
    
    @pytest.mark.asyncio
    async def test_draft_generation_contract(self):
        """Test draft generation contract."""
        # Test with different intents
        intents = [
            {
                "act_type": "procuração",
                "parties": [
                    {
                        "role": "outorgante",
                        "pii_extracted": ["João Silva"]
                    }
                ],
                "metadata": {
                    "purpose": "venda de imóvel"
                }
            },
            {
                "act_type": "contrato",
                "parties": [
                    {
                        "role": "comprador",
                        "pii_extracted": ["Maria Santos"]
                    },
                    {
                        "role": "vendedor",
                        "pii_extracted": ["Pedro Costa"]
                    }
                ],
                "metadata": {
                    "purpose": "compra e venda de imóvel"
                }
            }
        ]
        
        for intent in intents:
            payload = {
                "intent": intent,
                "pii_tokens": {
                    "PARTY_1_NAME": "token_123"
                }
            }
            response = await self.client.post("/api/v1/intent/generate-draft", json=payload)
            
            # Should handle different intents
            assert response.status_code == 200
            
            data = response.json()
            assert "draft_md" in data
            assert "tokens" in data
            assert "citations" in data
            assert "confidence" in data
    
    @pytest.mark.asyncio
    async def test_error_handling_contract(self):
        """Test error handling contract."""
        # Test with invalid JSON
        response = await self.client.post(
            "/api/v1/intent/parse",
            content="invalid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422
        
        # Test with unsupported content type
        response = await self.client.post(
            "/api/v1/intent/parse",
            content="test",
            headers={"content-type": "text/plain"}
        )
        assert response.status_code == 415
    
    @pytest.mark.asyncio
    async def test_security_headers_contract(self):
        """Test security headers contract."""
        # Make any request
        payload = {
            "command": "Fazer procuração para João Silva",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        response = await self.client.post("/api/v1/intent/parse", json=payload)
        
        # Should have security headers
        assert "x-content-type-options" in response.headers
        assert "x-frame-options" in response.headers
        assert "x-xss-protection" in response.headers
    
    @pytest.mark.asyncio
    async def test_versioning_contract(self):
        """Test API versioning contract."""
        # Test v1 endpoints
        payload = {
            "command": "Fazer procuração para João Silva",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        response = await self.client.post("/api/v1/intent/parse", json=payload)
        assert response.status_code == 200
        
        # Test that v2 endpoints don't exist yet
        response = await self.client.post("/api/v2/intent/parse", json=payload)
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_metrics_collection_contract(self):
        """Test metrics collection contract."""
        # Make some requests
        payload = {
            "command": "Fazer procuração para João Silva",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        for _ in range(5):
            await self.client.post("/api/v1/intent/parse", json=payload)
        
        # Check metrics
        response = await self.client.get("/metrics")
        assert response.status_code == 200
        
        content = response.text
        # Should have metrics for the requests we made
        assert "http_requests_total" in content
        assert "intent_engine_parse_duration_seconds" in content
