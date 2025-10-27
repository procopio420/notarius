"""
End-to-end tests for RAG evaluation system
"""

import pytest
import asyncio
import httpx
from unittest.mock import Mock, patch


class TestRAGEvaluationE2E:
    """Test RAG evaluation system end-to-end."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexnode_url = "http://localhost:8001"
        self.intent_engine_url = "http://localhost:8003"
        self.notarius_url = "http://localhost:8000"
        
        self.lexnode_client = httpx.AsyncClient(base_url=self.lexnode_url)
        self.intent_engine_client = httpx.AsyncClient(base_url=self.intent_engine_url)
        self.notarius_client = httpx.AsyncClient(base_url=self.notarius_url)
    
    @pytest.mark.asyncio
    async def test_rag_evaluation_workflow(self):
        """Test RAG evaluation workflow."""
        # 1. Test retrieval evaluation
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
        
        if retrieve_response.status_code == 200:
            retrieve_data = retrieve_response.json()
            
            # Evaluate retrieval results
            assert "results" in retrieve_data
            assert "total_count" in retrieve_data
            assert "query_time" in retrieve_data
            
            # Check result quality
            if retrieve_data["results"]:
                for result in retrieve_data["results"]:
                    assert "score" in result
                    assert 0.0 <= result["score"] <= 1.0
                    assert "title" in result
                    assert "content" in result
        
        # 2. Test grounded draft evaluation
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
        
        if draft_response.status_code == 200:
            draft_data = draft_response.json()
            
            # Evaluate draft quality
            assert "draft_md" in draft_data
            assert "citations" in draft_data
            assert "confidence" in draft_data
            assert "trace" in draft_data
            
            # Check confidence score
            assert 0.0 <= draft_data["confidence"] <= 1.0
            
            # Check citations quality
            if draft_data["citations"]:
                for citation in draft_data["citations"]:
                    assert "score" in citation
                    assert 0.0 <= citation["score"] <= 1.0
                    assert "uri" in citation
                    assert "anchor" in citation
                    assert "title" in citation
                    assert "snippet" in citation
    
    @pytest.mark.asyncio
    async def test_rag_evaluation_metrics(self):
        """Test RAG evaluation metrics."""
        # 1. Test retrieval metrics
        retrieve_payload = {
            "query": "procuração para venda de imóvel",
            "constraints": {"jurisdiction": "rj"},
            "top_k": 10
        }
        
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        
        if retrieve_response.status_code == 200:
            retrieve_data = retrieve_response.json()
            
            # Calculate hit@k metrics
            if retrieve_data["results"]:
                hit_at_1 = 1 if retrieve_data["results"][0]["score"] > 0.5 else 0
                hit_at_5 = sum(1 for r in retrieve_data["results"][:5] if r["score"] > 0.5)
                hit_at_10 = sum(1 for r in retrieve_data["results"] if r["score"] > 0.5)
                
                assert 0 <= hit_at_1 <= 1
                assert 0 <= hit_at_5 <= 5
                assert 0 <= hit_at_10 <= 10
            
            # Calculate nDCG metrics
            if retrieve_data["results"]:
                scores = [r["score"] for r in retrieve_data["results"]]
                ndcg = self._calculate_ndcg(scores)
                assert 0.0 <= ndcg <= 1.0
        
        # 2. Test grounded draft metrics
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
        
        if draft_response.status_code == 200:
            draft_data = draft_response.json()
            
            # Calculate grounding confidence
            grounding_confidence = draft_data["confidence"]
            assert 0.0 <= grounding_confidence <= 1.0
            
            # Calculate citation quality
            if draft_data["citations"]:
                citation_scores = [c["score"] for c in draft_data["citations"]]
                avg_citation_score = sum(citation_scores) / len(citation_scores)
                assert 0.0 <= avg_citation_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_rag_evaluation_golden_qa(self):
        """Test RAG evaluation with golden Q&A set."""
        # 1. Test with known good queries
        golden_queries = [
            {
                "query": "procuração para venda de imóvel",
                "expected_act_type": "procuração",
                "expected_entities": ["venda", "imóvel"]
            },
            {
                "query": "contrato de compra e venda",
                "expected_act_type": "contrato",
                "expected_entities": ["compra", "venda"]
            },
            {
                "query": "testamento",
                "expected_act_type": "testamento",
                "expected_entities": []
            }
        ]
        
        for golden_query in golden_queries:
            # Test retrieval
            retrieve_payload = {
                "query": golden_query["query"],
                "constraints": {"jurisdiction": "rj"},
                "top_k": 10
            }
            
            retrieve_response = await self.lexnode_client.post(
                "/api/v1/lexnode/retrieve",
                json=retrieve_payload
            )
            
            if retrieve_response.status_code == 200:
                retrieve_data = retrieve_response.json()
                
                # Check that results are relevant
                if retrieve_data["results"]:
                    for result in retrieve_data["results"]:
                        # Check that result contains expected entities
                        content = result["content"].lower()
                        for entity in golden_query["expected_entities"]:
                            assert entity.lower() in content or result["score"] > 0.3
            
            # Test intent parsing
            parse_payload = {
                "command": golden_query["query"],
                "tenant_context": {
                    "tenant_id": "test-tenant-123",
                    "user_id": "test-user-456"
                }
            }
            
            parse_response = await self.intent_engine_client.post(
                "/api/v1/intent/parse",
                json=parse_payload
            )
            
            if parse_response.status_code == 200:
                parse_data = parse_response.json()
                
                # Check that act_type is correctly identified
                intent = parse_data["intent"]
                if "act_type" in intent:
                    assert intent["act_type"] == golden_query["expected_act_type"]
    
    @pytest.mark.asyncio
    async def test_rag_evaluation_false_grounding(self):
        """Test RAG evaluation for false grounding detection."""
        # 1. Test with queries that should not be grounded
        ungrounded_queries = [
            "Como fazer um bolo de chocolate?",
            "Qual é a capital do Brasil?",
            "Receita de feijoada"
        ]
        
        for query in ungrounded_queries:
            # Test retrieval
            retrieve_payload = {
                "query": query,
                "constraints": {"jurisdiction": "rj"},
                "top_k": 10
            }
            
            retrieve_response = await self.lexnode_client.post(
                "/api/v1/lexnode/retrieve",
                json=retrieve_payload
            )
            
            if retrieve_response.status_code == 200:
                retrieve_data = retrieve_response.json()
                
                # Check that results have low scores
                if retrieve_data["results"]:
                    max_score = max(r["score"] for r in retrieve_data["results"])
                    assert max_score < 0.5  # Should have low relevance scores
            
            # Test intent parsing
            parse_payload = {
                "command": query,
                "tenant_context": {
                    "tenant_id": "test-tenant-123",
                    "user_id": "test-user-456"
                }
            }
            
            parse_response = await self.intent_engine_client.post(
                "/api/v1/intent/parse",
                json=parse_payload
            )
            
            if parse_response.status_code == 200:
                parse_data = parse_response.json()
                
                # Check that confidence is low
                assert parse_data["confidence"] < 0.5
    
    @pytest.mark.asyncio
    async def test_rag_evaluation_performance(self):
        """Test RAG evaluation performance."""
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
        
        if retrieve_response.status_code == 200:
            # Should respond within reasonable time
            assert retrieval_time < 5.0, f"Retrieval too slow: {retrieval_time}s"
            
            retrieve_data = retrieve_response.json()
            assert "query_time" in retrieve_data
            assert retrieve_data["query_time"] < 5.0
        
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
        
        if draft_response.status_code == 200:
            # Should respond within reasonable time
            assert draft_time < 10.0, f"Grounded draft too slow: {draft_time}s"
    
    @pytest.mark.asyncio
    async def test_rag_evaluation_consistency(self):
        """Test RAG evaluation consistency."""
        # 1. Test that same query returns consistent results
        query = "procuração para venda de imóvel"
        retrieve_payload = {
            "query": query,
            "constraints": {"jurisdiction": "rj"},
            "top_k": 10
        }
        
        # Make multiple requests
        responses = []
        for _ in range(3):
            response = await self.lexnode_client.post(
                "/api/v1/lexnode/retrieve",
                json=retrieve_payload
            )
            if response.status_code == 200:
                responses.append(response.json())
        
        if len(responses) >= 2:
            # Check that results are consistent
            first_response = responses[0]
            for response in responses[1:]:
                assert response["total_count"] == first_response["total_count"]
                
                # Check that top results are similar
                if first_response["results"] and response["results"]:
                    first_top_score = first_response["results"][0]["score"]
                    second_top_score = response["results"][0]["score"]
                    assert abs(first_top_score - second_top_score) < 0.1
    
    @pytest.mark.asyncio
    async def test_rag_evaluation_edge_cases(self):
        """Test RAG evaluation edge cases."""
        # 1. Test with empty query
        retrieve_payload = {
            "query": "",
            "constraints": {"jurisdiction": "rj"},
            "top_k": 10
        }
        
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        
        # Should return error or empty results
        assert retrieve_response.status_code in [200, 400, 422]
        
        if retrieve_response.status_code == 200:
            retrieve_data = retrieve_response.json()
            assert retrieve_data["total_count"] == 0
        
        # 2. Test with very long query
        long_query = "procuração " * 100
        retrieve_payload = {
            "query": long_query,
            "constraints": {"jurisdiction": "rj"},
            "top_k": 10
        }
        
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        
        # Should handle long query gracefully
        assert retrieve_response.status_code in [200, 400, 422]
        
        # 3. Test with special characters
        special_query = "procuração para venda de imóvel @#$%^&*()"
        retrieve_payload = {
            "query": special_query,
            "constraints": {"jurisdiction": "rj"},
            "top_k": 10
        }
        
        retrieve_response = await self.lexnode_client.post(
            "/api/v1/lexnode/retrieve",
            json=retrieve_payload
        )
        
        # Should handle special characters gracefully
        assert retrieve_response.status_code in [200, 400, 422]
    
    @pytest.mark.asyncio
    async def test_rag_evaluation_integration(self):
        """Test RAG evaluation integration with Notarius."""
        # 1. Generate minuta through Notarius
        command = "Fazer procuração para João Silva, CPF 123.456.789-00, outorgar poderes para vender imóvel em SP."
        
        generate_response = await self.notarius_client.post(
            "/api/v1/notarius/ai/generate/",
            json={"command": command, "processo_id": None}
        )
        
        if generate_response.status_code == 201:
            generate_data = generate_response.json()
            minuta_id = generate_data["minuta_id"]
            
            # 2. Evaluate minuta quality
            minuta_response = await self.notarius_client.get(f"/api/v1/notarius/minutas/{minuta_id}/")
            
            if minuta_response.status_code == 200:
                minuta_data = minuta_response.json()
                
                # Check grounding confidence
                assert minuta_data["grounding_confidence"] > 0.0
                assert minuta_data["grounding_confidence"] <= 1.0
                
                # Check citations quality
                if minuta_data["citations"]:
                    for citation in minuta_data["citations"]:
                        assert "score" in citation
                        assert 0.0 <= citation["score"] <= 1.0
                        assert "uri" in citation
                        assert "anchor" in citation
                        assert "title" in citation
                        assert "snippet" in citation
                
                # Check that PII is properly tokenized
                corpo_md = minuta_data["corpo_md"]
                assert "123.456.789-00" not in corpo_md
                assert "João Silva" not in corpo_md
                
                # Check that tokens are present
                variaveis_json = minuta_data["variaveis_json"]
                assert len(variaveis_json) > 0
    
    def _calculate_ndcg(self, scores):
        """Calculate nDCG for a list of scores."""
        if not scores:
            return 0.0
        
        # Simple nDCG calculation
        dcg = 0.0
        for i, score in enumerate(scores):
            dcg += score / (i + 1)
        
        # Ideal DCG (sorted scores)
        ideal_scores = sorted(scores, reverse=True)
        idcg = 0.0
        for i, score in enumerate(ideal_scores):
            idcg += score / (i + 1)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    @pytest.mark.asyncio
    async def test_rag_evaluation_metrics_collection(self):
        """Test RAG evaluation metrics collection."""
        # 1. Make requests to generate metrics
        try:
            # Test retrieval
            retrieve_payload = {
                "query": "procuração para venda de imóvel",
                "constraints": {"jurisdiction": "rj"},
                "top_k": 10
            }
            
            await self.lexnode_client.post(
                "/api/v1/lexnode/retrieve",
                json=retrieve_payload
            )
            
            # Test grounded draft
            draft_payload = {
                "act_type": "procuração",
                "variables": {
                    "PARTY_1_NAME": "João Silva"
                }
            }
            
            await self.lexnode_client.post(
                "/api/v1/lexnode/grounded-draft",
                json=draft_payload
            )
            
        except Exception:
            # Services might not be available, continue
            pass
        
        # 2. Check metrics
        try:
            metrics_response = await self.lexnode_client.get("/metrics")
            if metrics_response.status_code == 200:
                content = metrics_response.text
                assert "lexnode_retrieval_duration_seconds" in content
                assert "lexnode_grounding_confidence_score" in content
        except Exception:
            # Service might not be available, continue
            pass
    
    @pytest.mark.asyncio
    async def test_rag_evaluation_validation(self):
        """Test RAG evaluation validation."""
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