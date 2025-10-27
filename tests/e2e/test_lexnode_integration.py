"""
End-to-end tests for LexNode integration
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch


class TestLexNodeIntegrationE2E:
    """Test LexNode integration end-to-end."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexnode_url = "http://localhost:8001"
        self.notarius_url = "http://localhost:8000"
        
        self.lexnode_client = httpx.AsyncClient(base_url=self.lexnode_url)
        self.notarius_client = httpx.AsyncClient(base_url=self.notarius_url)
    
    @pytest.mark.asyncio
    async def test_lexnode_retrieval_workflow(self):
        """Test LexNode retrieval workflow."""
        # 1. Test retrieval endpoint
        retrieve_payload = {
            "query": "procuração para venda de imóvel",
            "constraints": {
                "jurisdiction": "rj",
                "document_type": "procuração"
            },
            "top_k": 10
        }
        
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        
        assert retrieve_response.status_code == 200
        retrieve_data = retrieve_response.json()
        
        assert "results" in retrieve_data
        assert "total_count" in retrieve_data
        assert "query_time" in retrieve_data
        assert isinstance(retrieve_data["results"], list)
        assert isinstance(retrieve_data["total_count"], int)
        assert isinstance(retrieve_data["query_time"], float)
        
        # 2. Verify result structure
        if retrieve_data["results"]:
            result = retrieve_data["results"][0]
            assert "id" in result
            assert "title" in result
            assert "content" in result
            assert "score" in result
            assert "metadata" in result
            
            # Check score is within valid range
            assert 0.0 <= result["score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_lexnode_grounded_draft_workflow(self):
        """Test LexNode grounded draft workflow."""
        # 1. Test grounded draft endpoint
        draft_payload = {
            "act_type": "procuração",
            "variables": {
                "PARTY_1_NAME": "João Silva",
                "PARTY_1_CPF": "123.456.789-00",
                "PROPERTY_ADDRESS": "Rua das Flores, 123"
            }
        }
        
        draft_response = await self.lexnode_client.post(
            "/api/v1/lexnode/grounded-draft",
            json=draft_payload
        )
        
        assert draft_response.status_code == 200
        draft_data = draft_response.json()
        
        assert "draft_md" in draft_data
        assert "citations" in draft_data
        assert "confidence" in draft_data
        assert "trace" in draft_data
        
        # 2. Verify draft structure
        assert isinstance(draft_data["draft_md"], str)
        assert isinstance(draft_data["citations"], list)
        assert isinstance(draft_data["confidence"], float)
        assert isinstance(draft_data["trace"], dict)
        
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
    async def test_lexnode_health_check(self):
        """Test LexNode health check."""
        # 1. Check health endpoint
        health_response = await self.lexnode_client.get("/health")
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert "status" in health_data
        assert health_data["status"] == "healthy"
        assert "database" in health_data
        assert "vector_store" in health_data
    
    @pytest.mark.asyncio
    async def test_lexnode_metrics_collection(self):
        """Test LexNode metrics collection."""
        # 1. Make some requests
        retrieve_payload = {
            "query": "procuração para venda de imóvel",
            "constraints": {"jurisdiction": "rj"},
            "top_k": 10
        }
        
        for _ in range(5):
            await self.lexnode_client.post(
                "/api/v1/lexnode/retrieve",
                json=retrieve_payload
            )
        
        # 2. Check metrics
        metrics_response = await self.lexnode_client.get("/metrics")
        assert metrics_response.status_code == 200
        
        metrics_content = metrics_response.text
        assert "http_requests_total" in metrics_content
        assert "lexnode_retrieval_duration_seconds" in metrics_content
        assert "lexnode_grounding_confidence_score" in metrics_content
    
    @pytest.mark.asyncio
    async def test_lexnode_error_handling(self):
        """Test LexNode error handling."""
        # 1. Test with invalid query
        retrieve_payload = {
            "query": "",
            "constraints": {"jurisdiction": "rj"},
            "top_k": 10
        }
        
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        
        # Should return error
        assert retrieve_response.status_code >= 400
        
        # 2. Test with missing constraints
        retrieve_payload = {
            "query": "procuração para venda de imóvel",
            "top_k": 10
        }
        
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        
        # Should return validation error
        assert retrieve_response.status_code == 422
        
        # 3. Test with invalid act_type
        draft_payload = {
            "act_type": "",
            "variables": {
                "PARTY_1_NAME": "João Silva"
            }
        }
        
        draft_response = await self.lexnode_client.post(
            "/api/v1/lexnode/grounded-draft",
            json=draft_payload
        )
        
        # Should return validation error
        assert draft_response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_lexnode_performance(self):
        """Test LexNode performance."""
        import time
        
        # 1. Test retrieval performance
        retrieve_payload = {
            "query": "procuração para venda de imóvel",
            "constraints": {"jurisdiction": "rj"},
            "top_k": 10
        }
        
        start_time = time.time()
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        retrieval_time = time.time() - start_time
        
        assert retrieve_response.status_code == 200
        assert retrieval_time < 5.0, f"Retrieval too slow: {retrieval_time}s"
        
        # 2. Test grounded draft performance
        draft_payload = {
            "act_type": "procuração",
            "variables": {
                "PARTY_1_NAME": "João Silva"
            }
        }
        
        start_time = time.time()
        draft_response = await self.lexnode_client.post(
            "/api/v1/lexnode/grounded-draft",
            json=draft_payload
        )
        draft_time = time.time() - start_time
        
        assert draft_response.status_code == 200
        assert draft_time < 10.0, f"Grounded draft too slow: {draft_time}s"
    
    @pytest.mark.asyncio
    async def test_lexnode_concurrent_operations(self):
        """Test LexNode concurrent operations."""
        import asyncio
        
        # 1. Test concurrent retrieval
        async def retrieve_documents(i):
            payload = {
                "query": f"procuração {i}",
                "constraints": {"jurisdiction": "rj"},
                "top_k": 10
            }
            return await self.lexnode_client.post(
                "/api/v1/lexnode/retrieve",
                json=payload
            )
        
        # Run 10 concurrent retrievals
        tasks = [retrieve_documents(i) for i in range(10)]
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            
            data = response.json()
            assert "results" in data
            assert "total_count" in data
        
        # 2. Test concurrent grounded draft
        async def generate_draft(i):
            payload = {
                "act_type": "procuração",
                "variables": {
                    f"PARTY_{i}_NAME": f"Pessoa {i}"
                }
            }
            return await self.lexnode_client.post(
                "/api/v1/lexnode/grounded-draft",
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
    async def test_lexnode_search_constraints(self):
        """Test LexNode search constraints."""
        # 1. Test with different constraint types
        constraints_tests = [
            {"jurisdiction": "rj"},
            {"document_type": "procuração"},
            {"date_range": {"start": "2023-01-01", "end": "2023-12-31"}},
            {"keywords": ["venda", "imóvel"]},
            {"authority": "CNJ"}
        ]
        
        for constraints in constraints_tests:
            retrieve_payload = {
                "query": "procuração para venda de imóvel",
                "constraints": constraints,
                "top_k": 10
            }
            
            retrieve_response = await self.lexnode_client.post(
                "/api/v1/lexnode/retrieve",
                json=retrieve_payload
            )
            
            # Should handle different constraint types
            assert retrieve_response.status_code == 200
            
            data = retrieve_response.json()
            assert "results" in data
            assert "total_count" in data
    
    @pytest.mark.asyncio
    async def test_lexnode_act_types(self):
        """Test LexNode different act types."""
        # 1. Test with different act types
        act_types = [
            "procuração",
            "contrato",
            "testamento",
            "escritura",
            "certidão"
        ]
        
        for act_type in act_types:
            draft_payload = {
                "act_type": act_type,
                "variables": {
                    "PARTY_1_NAME": "João Silva"
                }
            }
            
            draft_response = await self.lexnode_client.post(
                "/api/v1/lexnode/grounded-draft",
                json=draft_payload
            )
            
            # Should handle different act types
            assert draft_response.status_code == 200
            
            data = draft_response.json()
            assert "draft_md" in data
            assert "citations" in data
            assert "confidence" in data
    
    @pytest.mark.asyncio
    async def test_lexnode_pagination(self):
        """Test LexNode pagination."""
        # 1. Test with different top_k values
        top_k_values = [1, 5, 10, 50, 100]
        
        for top_k in top_k_values:
            retrieve_payload = {
                "query": "procuração para venda de imóvel",
                "constraints": {"jurisdiction": "rj"},
                "top_k": top_k
            }
            
            retrieve_response = await self.lexnode_client.post(
                "/api/v1/lexnode/retrieve",
                json=retrieve_payload
            )
            
            # Should handle different top_k values
            assert retrieve_response.status_code == 200
            
            data = retrieve_response.json()
            assert "results" in data
            assert "total_count" in data
            assert len(data["results"]) <= top_k
    
    @pytest.mark.asyncio
    async def test_lexnode_confidence_scores(self):
        """Test LexNode confidence scores."""
        # 1. Test retrieval confidence scores
        retrieve_payload = {
            "query": "procuração para venda de imóvel",
            "constraints": {"jurisdiction": "rj"},
            "top_k": 10
        }
        
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        
        data = retrieve_response.json()
        if data["results"]:
            for result in data["results"]:
                assert "score" in result
                assert isinstance(result["score"], (int, float))
                assert 0.0 <= result["score"] <= 1.0
        
        # 2. Test grounded draft confidence scores
        draft_payload = {
            "act_type": "procuração",
            "variables": {
                "PARTY_1_NAME": "João Silva"
            }
        }
        
        draft_response = await self.lexnode_client.post(
            "/api/v1/lexnode/grounded-draft",
            json=draft_payload
        )
        
        data = draft_response.json()
        assert "confidence" in data
        assert isinstance(data["confidence"], (int, float))
        assert 0.0 <= data["confidence"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_lexnode_citation_structure(self):
        """Test LexNode citation structure."""
        # 1. Test grounded draft citations
        draft_payload = {
            "act_type": "procuração",
            "variables": {
                "PARTY_1_NAME": "João Silva"
            }
        }
        
        draft_response = await self.lexnode_client.post(
            "/api/v1/lexnode/grounded-draft",
            json=draft_payload
        )
        
        data = draft_response.json()
        if data["citations"]:
            citation = data["citations"][0]
            
            # Required fields
            assert "uri" in citation
            assert "anchor" in citation
            assert "title" in citation
            assert "snippet" in citation
            assert "score" in citation
            
            # Field types
            assert isinstance(citation["uri"], str)
            assert isinstance(citation["anchor"], str)
            assert isinstance(citation["title"], str)
            assert isinstance(citation["snippet"], str)
            assert isinstance(citation["score"], (int, float))
            
            # Field values
            assert len(citation["uri"]) > 0
            assert len(citation["anchor"]) > 0
            assert len(citation["title"]) > 0
            assert len(citation["snippet"]) > 0
            assert 0.0 <= citation["score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_lexnode_trace_structure(self):
        """Test LexNode trace structure."""
        # 1. Test grounded draft trace
        draft_payload = {
            "act_type": "procuração",
            "variables": {
                "PARTY_1_NAME": "João Silva"
            }
        }
        
        draft_response = await self.lexnode_client.post(
            "/api/v1/lexnode/grounded-draft",
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
    async def test_lexnode_integration_with_notarius(self):
        """Test LexNode integration with Notarius."""
        # 1. Generate minuta through Notarius (which uses LexNode)
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
        
        # 2. Verify minuta has LexNode data
        minuta_response = await self.notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
        assert minuta_response.status_code == 200
        
        minuta_data = minuta_response.json()
        assert minuta_data["citations"] is not None
        assert len(minuta_data["citations"]) > 0
        assert minuta_data["grounding_confidence"] > 0.0
        assert minuta_data["lexnode_trace"] is not None
        
        # 3. Verify citation structure
        citation = minuta_data["citations"][0]
        assert "uri" in citation
        assert "anchor" in citation
        assert "title" in citation
        assert "snippet" in citation
        assert "score" in citation
    
    @pytest.mark.asyncio
    async def test_lexnode_security(self):
        """Test LexNode security."""
        # 1. Test with invalid constraints
        retrieve_payload = {
            "query": "procuração para venda de imóvel",
            "constraints": {
                "jurisdiction": "invalid-jurisdiction"
            },
            "top_k": 10
        }
        
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        
        # Should handle invalid constraints gracefully
        assert retrieve_response.status_code in [200, 400, 422]
        
        # 2. Test with invalid act_type
        draft_payload = {
            "act_type": "invalid-act-type",
            "variables": {
                "PARTY_1_NAME": "João Silva"
            }
        }
        
        draft_response = await self.lexnode_client.post(
            "/api/v1/lexnode/grounded-draft",
            json=draft_payload
        )
        
        # Should handle invalid act_type gracefully
        assert draft_response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    async def test_lexnode_validation(self):
        """Test LexNode validation."""
        # 1. Test with missing query
        retrieve_payload = {
            "constraints": {"jurisdiction": "rj"},
            "top_k": 10
        }
        
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        
        # Should return validation error
        assert retrieve_response.status_code == 422
        
        # 2. Test with missing constraints
        retrieve_payload = {
            "query": "procuração para venda de imóvel",
            "top_k": 10
        }
        
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        
        # Should return validation error
        assert retrieve_response.status_code == 422
        
        # 3. Test with invalid top_k
        retrieve_payload = {
            "query": "procuração para venda de imóvel",
            "constraints": {"jurisdiction": "rj"},
            "top_k": -1
        }
        
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        
        # Should return validation error
        assert retrieve_response.status_code == 422
