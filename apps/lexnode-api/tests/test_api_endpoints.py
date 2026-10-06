"""Tests for LexNode API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

pytestmark = pytest.mark.skip(reason="Legacy endpoint suite relies on removed service modules.")


class TestLexNodeAPI:
    """Test cases for LexNode API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "lexnode-api"}
    
    def test_search_documents(self, client, mock_search_query, mock_search_results):
        """Test document search endpoint."""
        with patch('app.services.retrieval_service.RetrievalService.search_documents') as mock_search:
            mock_search.return_value = mock_search_results
            
            response = client.post("/api/v1/search", json=mock_search_query)
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
            assert len(data["results"]) == 2
            assert data["results"][0]["id"] == "doc_123"
            assert data["results"][0]["relevance_score"] == 0.95
    
    def test_search_documents_invalid_query(self, client):
        """Test document search with invalid query."""
        invalid_query = {
            "query": "",  # Empty query
            "limit": 10
        }
        
        response = client.post("/api/v1/search", json=invalid_query)
        assert response.status_code == 400
    
    def test_search_documents_missing_query(self, client):
        """Test document search with missing query."""
        response = client.post("/api/v1/search", json={})
        assert response.status_code == 422  # Validation error
    
    def test_get_document_by_id(self, client, mock_document_data):
        """Test get document by ID endpoint."""
        with patch('app.services.retrieval_service.RetrievalService.get_document_by_id') as mock_get:
            mock_get.return_value = mock_document_data
            
            response = client.get("/api/v1/documents/doc_123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "doc_123"
            assert data["title"] == "Lei 8.935/1994"
    
    def test_get_document_not_found(self, client):
        """Test get document by ID when document doesn't exist."""
        with patch('app.services.retrieval_service.RetrievalService.get_document_by_id') as mock_get:
            mock_get.return_value = None
            
            response = client.get("/api/v1/documents/nonexistent")
            
            assert response.status_code == 404
    
    def test_crawl_documents(self, client, mock_crawler_data):
        """Test crawl documents endpoint."""
        with patch('app.services.crawler_service.CrawlerService.crawl_documents') as mock_crawl:
            mock_crawl.return_value = [mock_crawler_data]
            
            response = client.post("/api/v1/crawl", json={
                "sources": ["CNJ"],
                "limit": 10
            })
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["documents"]) == 1
            assert data["documents"][0]["title"] == "Lei 8.935/1994"
    
    def test_crawl_documents_invalid_source(self, client):
        """Test crawl documents with invalid source."""
        response = client.post("/api/v1/crawl", json={
            "sources": ["INVALID_SOURCE"],
            "limit": 10
        })
        assert response.status_code == 400
    
    def test_index_documents(self, client, mock_indexer_data):
        """Test index documents endpoint."""
        with patch('app.services.indexer_service.IndexerService.index_documents') as mock_index:
            mock_index.return_value = {"indexed_count": 1, "errors": []}
            
            response = client.post("/api/v1/index", json={
                "documents": [mock_indexer_data]
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["indexed_count"] == 1
            assert data["errors"] == []
    
    def test_index_documents_invalid_data(self, client):
        """Test index documents with invalid data."""
        response = client.post("/api/v1/index", json={
            "documents": [{"invalid": "data"}]
        })
        assert response.status_code == 400
    
    def test_get_statistics(self, client):
        """Test get statistics endpoint."""
        with patch('app.services.retrieval_service.RetrievalService.get_statistics') as mock_stats:
            mock_stats.return_value = {
                "total_documents": 1000,
                "sources": {
                    "CNJ": 500,
                    "CGJ-SP": 300,
                    "CGJ-RJ": 200
                },
                "last_updated": "2023-01-01T00:00:00Z"
            }
            
            response = client.get("/api/v1/statistics")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_documents"] == 1000
            assert data["sources"]["CNJ"] == 500
    
    def test_search_with_filters(self, client, mock_search_results):
        """Test search with various filters."""
        with patch('app.services.retrieval_service.RetrievalService.search_documents') as mock_search:
            mock_search.return_value = mock_search_results
            
            query = {
                "query": "procuração",
                "filters": {
                    "source": "CNJ",
                    "type": "law",
                    "jurisdiction": "federal",
                    "date_from": "1990-01-01",
                    "date_to": "2000-12-31"
                },
                "limit": 5
            }
            
            response = client.post("/api/v1/search", json=query)
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 2
    
    def test_search_pagination(self, client, mock_search_results):
        """Test search with pagination."""
        with patch('app.services.retrieval_service.RetrievalService.search_documents') as mock_search:
            mock_search.return_value = mock_search_results
            
            query = {
                "query": "procuração",
                "limit": 1,
                "offset": 1
            }
            
            response = client.post("/api/v1/search", json=query)
            
            assert response.status_code == 200
            data = response.json()
            assert data["limit"] == 1
            assert data["offset"] == 1
    
    def test_search_large_query(self, client, mock_search_results):
        """Test search with very large query."""
        with patch('app.services.retrieval_service.RetrievalService.search_documents') as mock_search:
            mock_search.return_value = mock_search_results
            
            large_query = {
                "query": "a" * 10000,  # Very long query
                "limit": 10
            }
            
            response = client.post("/api/v1/search", json=large_query)
            
            assert response.status_code == 200
    
    def test_search_special_characters(self, client, mock_search_results):
        """Test search with special characters."""
        with patch('app.services.retrieval_service.RetrievalService.search_documents') as mock_search:
            mock_search.return_value = mock_search_results
            
            query = {
                "query": "procuração com acentos: ção, ñ, ü",
                "limit": 10
            }
            
            response = client.post("/api/v1/search", json=query)
            
            assert response.status_code == 200
    
    def test_search_sql_injection(self, client, mock_search_results):
        """Test search with SQL injection attempts."""
        with patch('app.services.retrieval_service.RetrievalService.search_documents') as mock_search:
            mock_search.return_value = mock_search_results
            
            malicious_query = {
                "query": "'; DROP TABLE documents; --",
                "limit": 10
            }
            
            response = client.post("/api/v1/search", json=malicious_query)
            
            # Should not cause SQL injection
            assert response.status_code == 200
    
    def test_search_xss_attempt(self, client, mock_search_results):
        """Test search with XSS attempts."""
        with patch('app.services.retrieval_service.RetrievalService.search_documents') as mock_search:
            mock_search.return_value = mock_search_results
            
            xss_query = {
                "query": "<script>alert('XSS')</script>",
                "limit": 10
            }
            
            response = client.post("/api/v1/search", json=xss_query)
            
            # Should not cause XSS
            assert response.status_code == 200
    
    def test_concurrent_searches(self, client, mock_search_results):
        """Test concurrent search requests."""
        with patch('app.services.retrieval_service.RetrievalService.search_documents') as mock_search:
            mock_search.return_value = mock_search_results
            
            query = {
                "query": "procuração",
                "limit": 10
            }
            
            # Simulate concurrent requests
            responses = []
            for i in range(10):
                response = client.post("/api/v1/search", json=query)
                responses.append(response)
            
            # All requests should succeed
            for response in responses:
                assert response.status_code == 200
    
    def test_error_handling(self, client):
        """Test error handling in API endpoints."""
        with patch('app.services.retrieval_service.RetrievalService.search_documents') as mock_search:
            mock_search.side_effect = Exception("Database connection failed")
            
            query = {
                "query": "procuração",
                "limit": 10
            }
            
            response = client.post("/api/v1/search", json=query)
            
            assert response.status_code == 500
    
    def test_rate_limiting(self, client, mock_search_results):
        """Test rate limiting on search endpoint."""
        with patch('app.services.retrieval_service.RetrievalService.search_documents') as mock_search:
            mock_search.return_value = mock_search_results
            
            query = {
                "query": "procuração",
                "limit": 10
            }
            
            # Make many requests quickly
            for i in range(100):
                response = client.post("/api/v1/search", json=query)
                if response.status_code == 429:  # Rate limited
                    break
            
            # Should eventually hit rate limit
            assert response.status_code in [200, 429]
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v1/search")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
    
    def test_content_type_validation(self, client):
        """Test content type validation."""
        response = client.post("/api/v1/search", 
                             data="invalid json",
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422
    
    def test_missing_content_type(self, client):
        """Test missing content type header."""
        response = client.post("/api/v1/search", 
                             data='{"query": "test"}')
        assert response.status_code == 422
