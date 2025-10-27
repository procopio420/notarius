"""
End-to-end tests for Intent Engine integration
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch


class TestIntentEngineIntegrationE2E:
    """Test Intent Engine integration end-to-end."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.intent_engine_url = "http://localhost:8003"
        self.notarius_url = "http://localhost:8000"
        
        self.intent_engine_client = httpx.AsyncClient(base_url=self.intent_engine_url)
        self.notarius_client = httpx.AsyncClient(base_url=self.notarius_url)
    
    @pytest.mark.asyncio
    async def test_intent_engine_parse_workflow(self):
        """Test Intent Engine parse workflow."""
        # 1. Test parse intent endpoint
        parse_payload = {
            "command": "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em SP.",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        parse_response = await self.intent_engine_client.post(
            "/api/v1/intent/parse",
            json=parse_payload
        )
        
        assert parse_response.status_code == 200
        parse_data = parse_response.json()
        
        assert "intent" in parse_data
        assert "pii_extracted" in parse_data
        assert "confidence" in parse_data
        assert "trace" in parse_data
        
        # 2. Verify intent structure
        intent = parse_data["intent"]
        assert "act_type" in intent
        assert "parties" in intent
        assert "metadata" in intent
        assert isinstance(intent["act_type"], str)
        assert isinstance(intent["parties"], list)
        assert isinstance(intent["metadata"], dict)
        
        # 3. Verify PII extracted structure
        pii_extracted = parse_data["pii_extracted"]
        assert isinstance(pii_extracted, list)
        if pii_extracted:
            pii_item = pii_extracted[0]
            assert "value" in pii_item
            assert "type" in pii_item
            assert "confidence" in pii_item
        
        # 4. Verify confidence is within valid range
        assert 0.0 <= parse_data["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_intent_engine_generate_draft_workflow(self):
        """Test Intent Engine generate draft workflow."""
        # 1. Test generate draft endpoint
        draft_payload = {
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
        
        draft_response = await self.intent_engine_client.post(
            "/api/v1/intent/generate-draft",
            json=draft_payload
        )
        
        assert draft_response.status_code == 200
        draft_data = draft_response.json()
        
        assert "draft_md" in draft_data
        assert "tokens" in draft_data
        assert "citations" in draft_data
        assert "confidence" in draft_data
        assert "trace" in draft_data
        assert "cache_key" in draft_data
        
        # 2. Verify draft structure
        assert isinstance(draft_data["draft_md"], str)
        assert isinstance(draft_data["tokens"], dict)
        assert isinstance(draft_data["citations"], list)
        assert isinstance(draft_data["confidence"], float)
        assert isinstance(draft_data["trace"], dict)
        assert isinstance(draft_data["cache_key"], str)
        
        # 3. Verify confidence is within valid range
        assert 0.0 <= draft_data["confidence"] <= 1.0
        
        # 4. Verify citations structure
        if draft_data["citations"]:
            citation = draft_data["citations"][0]
            assert "uri" in citation
            assert "anchor" in citation
            assert "title" in citation
            assert "snippet" in citation
            assert "score" in citation
            
            # Check citation score is within valid range
            assert 0.0 <= citation["score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_intent_engine_health_check(self):
        """Test Intent Engine health check."""
        # 1. Check health endpoint
        health_response = await self.intent_engine_client.get("/health")
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert "status" in health_data
        assert health_data["status"] == "healthy"
        assert "llm_provider" in health_data
        assert "model_version" in health_data
    
    @pytest.mark.asyncio
    async def test_intent_engine_metrics_collection(self):
        """Test Intent Engine metrics collection."""
        # 1. Make some requests
        parse_payload = {
            "command": "Fazer procuração para João Silva",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        for _ in range(5):
            await self.intent_engine_client.post(
                "/api/v1/intent/parse",
                json=parse_payload
            )
        
        # 2. Check metrics
        metrics_response = await self.intent_engine_client.get("/metrics")
        assert metrics_response.status_code == 200
        
        metrics_content = metrics_response.text
        assert "http_requests_total" in metrics_content
        assert "intent_engine_parse_duration_seconds" in metrics_content
        assert "intent_engine_generate_draft_duration_seconds" in metrics_content
    
    @pytest.mark.asyncio
    async def test_intent_engine_error_handling(self):
        """Test Intent Engine error handling."""
        # 1. Test with invalid command
        parse_payload = {
            "command": "",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        parse_response = await self.intent_engine_client.post(
            "/api/v1/intent/parse",
            json=parse_payload
        )
        
        # Should return error
        assert parse_response.status_code >= 400
        
        # 2. Test with missing tenant_context
        parse_payload = {
            "command": "Fazer procuração para João Silva"
        }
        
        parse_response = await self.intent_engine_client.post(
            "/api/v1/intent/parse",
            json=parse_payload
        )
        
        # Should return validation error
        assert parse_response.status_code == 422
        
        # 3. Test with invalid intent structure
        draft_payload = {
            "intent": "invalid",
            "pii_tokens": {
                "PARTY_1_NAME": "token_123"
            }
        }
        
        draft_response = await self.intent_engine_client.post(
            "/api/v1/intent/generate-draft",
            json=draft_payload
        )
        
        # Should return validation error
        assert draft_response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_intent_engine_performance(self):
        """Test Intent Engine performance."""
        import time
        
        # 1. Test parse intent performance
        parse_payload = {
            "command": "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em SP.",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        start_time = time.time()
        parse_response = await self.intent_engine_client.post(
            "/api/v1/intent/parse",
            json=parse_payload
        )
        parse_time = time.time() - start_time
        
        assert parse_response.status_code == 200
        assert parse_time < 10.0, f"Parse intent too slow: {parse_time}s"
        
        # 2. Test generate draft performance
        draft_payload = {
            "intent": {
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
            "pii_tokens": {
                "PARTY_1_NAME": "token_123"
            }
        }
        
        start_time = time.time()
        draft_response = await self.intent_engine_client.post(
            "/api/v1/intent/generate-draft",
            json=draft_payload
        )
        draft_time = time.time() - start_time
        
        assert draft_response.status_code == 200
        assert draft_time < 15.0, f"Generate draft too slow: {draft_time}s"
    
    @pytest.mark.asyncio
    async def test_intent_engine_concurrent_operations(self):
        """Test Intent Engine concurrent operations."""
        import asyncio
        
        # 1. Test concurrent parse intent
        async def parse_intent(i):
            payload = {
                "command": f"Fazer procuração para Pessoa {i}",
                "tenant_context": {
                    "tenant_id": "test-tenant-123",
                    "user_id": "test-user-456"
                }
            }
            return await self.intent_engine_client.post(
                "/api/v1/intent/parse",
                json=payload
            )
        
        # Run 10 concurrent parse intents
        tasks = [parse_intent(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            
            data = response.json()
            assert "intent" in data
            assert "pii_extracted" in data
        
        # 2. Test concurrent generate draft
        async def generate_draft(i):
            payload = {
                "intent": {
                    "act_type": "procuração",
                    "parties": [
                        {
                            "role": "outorgante",
                            "pii_extracted": [f"Pessoa {i}"]
                        }
                    ],
                    "metadata": {
                        "purpose": "venda de imóvel"
                    }
                },
                "pii_tokens": {
                    f"PARTY_{i}_NAME": f"token_{i}"
                }
            }
            return await self.intent_engine_client.post(
                "/api/v1/intent/generate-draft",
                json=payload
            )
        
        # Run 10 concurrent draft generations
        tasks = [generate_draft(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            
            data = response.json()
            assert "draft_md" in data
            assert "citations" in data
            assert "confidence" in data
    
    @pytest.mark.asyncio
    async def test_intent_engine_act_types(self):
        """Test Intent Engine different act types."""
        # 1. Test with different act types
        commands = [
            "Fazer procuração para João Silva",
            "Fazer contrato de compra e venda",
            "Fazer testamento",
            "Fazer escritura de imóvel",
            "Fazer certidão de nascimento"
        ]
        
        for command in commands:
            parse_payload = {
                "command": command,
                "tenant_context": {
                    "tenant_id": "test-tenant-123",
                    "user_id": "test-user-456"
                }
            }
            
            parse_response = await self.intent_engine_client.post(
                "/api/v1/intent/parse",
                json=parse_payload
            )
            
            # Should handle different act types
            assert parse_response.status_code == 200
            
            data = parse_response.json()
            assert "intent" in data
            assert "act_type" in data["intent"]
    
    @pytest.mark.asyncio
    async def test_intent_engine_pii_extraction(self):
        """Test Intent Engine PII extraction."""
        # 1. Test with different PII types
        commands = [
            "Fazer procuração para João Silva, CPF 123.456.789-00",
            "Fazer contrato com Maria Santos, email: maria@email.com",
            "Fazer testamento de Pedro Costa, telefone: (11) 99999-9999",
            "Fazer escritura de imóvel em Rua das Flores, 123"
        ]
        
        for command in commands:
            parse_payload = {
                "command": command,
                "tenant_context": {
                    "tenant_id": "test-tenant-123",
                    "user_id": "test-user-456"
                }
            }
            
            parse_response = await self.intent_engine_client.post(
                "/api/v1/intent/parse",
                json=parse_payload
            )
            
            # Should handle different PII types
            assert parse_response.status_code == 200
            
            data = parse_response.json()
            assert "pii_extracted" in data
            assert isinstance(data["pii_extracted"], list)
    
    @pytest.mark.asyncio
    async def test_intent_engine_confidence_scores(self):
        """Test Intent Engine confidence scores."""
        # 1. Test parse intent confidence scores
        parse_payload = {
            "command": "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em SP.",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        parse_response = await self.intent_engine_client.post(
            "/api/v1/intent/parse",
            json=parse_payload
        )
        
        data = parse_response.json()
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0
        
        # 2. Test generate draft confidence scores
        draft_payload = {
            "intent": {
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
            "pii_tokens": {
                "PARTY_1_NAME": "token_123"
            }
        }
        
        draft_response = await self.intent_engine_client.post(
            "/api/v1/intent/generate-draft",
            json=draft_payload
        )
        
        data = draft_response.json()
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_intent_engine_trace_structure(self):
        """Test Intent Engine trace structure."""
        # 1. Test parse intent trace
        parse_payload = {
            "command": "Fazer procuração para João Silva",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        parse_response = await self.intent_engine_client.post(
            "/api/v1/intent/parse",
            json=parse_payload
        )
        
        data = parse_response.json()
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
        
        # 2. Test generate draft trace
        draft_payload = {
            "intent": {
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
            "pii_tokens": {
                "PARTY_1_NAME": "token_123"
            }
        }
        
        draft_response = await self.intent_engine_client.post(
            "/api/v1/intent/generate-draft",
            json=draft_payload
        )
        
        data = draft_response.json()
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
    async def test_intent_engine_draft_generation(self):
        """Test Intent Engine draft generation."""
        # 1. Test with different intents
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
            draft_payload = {
                "intent": intent,
                "pii_tokens": {
                    "PARTY_1_NAME": "token_123"
                }
            }
            
            draft_response = await self.intent_engine_client.post(
                "/api/v1/intent/generate-draft",
                json=draft_payload
            )
            
            # Should handle different intents
            assert draft_response.status_code == 200
            
            data = draft_response.json()
            assert "draft_md" in data
            assert "tokens" in data
            assert "citations" in data
            assert "confidence" in data
    
    @pytest.mark.asyncio
    async def test_intent_engine_integration_with_notarius(self):
        """Test Intent Engine integration with Notarius."""
        # 1. Generate minuta through Notarius (which uses Intent Engine)
        command = "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em SP."
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json={"command": command, "processo_id": None}
        )
        
        assert generate_response.status_code == 201
        generate_data = generate_response.json()
        
        minuta_id = generate_data["minuta_id"]
        assert minuta_id is not None
        assert generate_data["confidence"] > 0.0
        assert generate_data["citations_count"] > 0
        
        # 2. Verify minuta has Intent Engine data
        minuta_response = await self.notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
        assert minuta_response.status_code == 200
        
        minuta_data = minuta_response.json()
        assert minuta_data["corpo_md"] is not None
        assert minuta_data["variaveis_json"] is not None
        assert minuta_data["citations"] is not None
        assert len(minuta_data["citations"]) > 0
        assert minuta_data["grounding_confidence"] > 0.0
        assert minuta_data["lexnode_trace"] is not None
        
        # 3. Verify PII is tokenized
        corpo_md = minuta_data["corpo_md"]
        assert "123.456.789-00" not in corpo_md  # CPF should be tokenized
        assert "João Silva" not in corpo_md  # Name should be tokenized
        
        # 4. Verify tokens are present
        variaveis_json = minuta_data["variaveis_json"]
        assert len(variaveis_json) > 0
        
        # 5. Verify citation structure
        citation = minuta_data["citations"][0]
        assert "uri" in citation
        assert "anchor" in citation
        assert "title" in citation
        assert "snippet" in citation
        assert "score" in citation
    
    @pytest.mark.asyncio
    async def test_intent_engine_security(self):
        """Test Intent Engine security."""
        # 1. Test with invalid tenant context
        parse_payload = {
            "command": "Fazer procuração para João Silva",
            "tenant_context": {
                "tenant_id": "invalid-tenant",
                "user_id": "invalid-user"
            }
        }
        
        parse_response = await self.intent_engine_client.post(
            "/api/v1/intent/parse",
            json=parse_payload
        )
        
        # Should handle invalid tenant context gracefully
        assert parse_response.status_code in [200, 400, 403]
        
        # 2. Test with malicious command
        malicious_command = "DROP TABLE users; Fazer procuração para João Silva"
        
        parse_payload = {
            "command": malicious_command,
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        parse_response = await self.intent_engine_client.post(
            "/api/v1/intent/parse",
            json=parse_payload
        )
        
        # Should handle malicious command gracefully
        assert parse_response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    async def test_intent_engine_validation(self):
        """Test Intent Engine validation."""
        # 1. Test with missing command
        parse_payload = {
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        parse_response = await self.intent_engine_client.post(
            "/api/v1/intent/parse",
            json=parse_payload
        )
        
        # Should return validation error
        assert parse_response.status_code == 422
        
        # 2. Test with missing tenant_context
        parse_payload = {
            "command": "Fazer procuração para João Silva"
        }
        
        parse_response = await self.intent_engine_client.post(
            "/api/v1/intent/parse",
            json=parse_payload
        )
        
        # Should return validation error
        assert parse_response.status_code == 422
        
        # 3. Test with empty command
        parse_payload = {
            "command": "",
            "tenant_context": {
                "tenant_id": "test-tenant-123",
                "user_id": "test-user-456"
            }
        }
        
        parse_response = await self.intent_engine_client.post(
            "/api/v1/intent/parse",
            json=parse_payload
        )
        
        # Should return validation error
        assert parse_response.status_code == 422
        
        # 4. Test with missing intent
        draft_payload = {
            "pii_tokens": {
                "PARTY_1_NAME": "token_123"
            }
        }
        
        draft_response = await self.intent_engine_client.post(
            "/api/v1/intent/generate-draft",
            json=draft_payload
        )
        
        # Should return validation error
        assert draft_response.status_code == 422
        
        # 5. Test with missing pii_tokens
        draft_payload = {
            "intent": {
                "act_type": "procuração",
                "parties": [],
                "metadata": {}
            }
        }
        
        draft_response = await self.intent_engine_client.post(
            "/api/v1/intent/generate-draft",
            json=draft_payload
        )
        
        # Should return validation error
        assert draft_response.status_code == 422
