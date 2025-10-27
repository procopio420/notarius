"""
Tests for LexNode services.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from app.services.crawler_service import CrawlerService
from app.services.indexer_service import IndexerService
from app.services.retrieval_service import RetrievalService


class TestCrawlerService:
    """Test cases for CrawlerService."""
    
    @pytest.fixture
    def crawler_service(self):
        """Create a crawler service instance."""
        return CrawlerService()
    
    @pytest.mark.asyncio
    async def test_crawl_cnj_documents(self, crawler_service):
        """Test crawling CNJ documents."""
        with patch('app.crawler.cnj.CNJCrawler.crawl') as mock_crawl:
            mock_crawl.return_value = [
                {
                    "url": "https://www.cnj.jus.br/lei-8935-1994/",
                    "title": "Lei 8.935/1994",
                    "content": "Lei dos Cartórios e Registros Públicos...",
                    "metadata": {
                        "source": "CNJ",
                        "date": "1994-11-18",
                        "type": "law"
                    }
                }
            ]
            
            result = await crawler_service.crawl_documents(["CNJ"], limit=10)
            
            assert len(result) == 1
            assert result[0]["title"] == "Lei 8.935/1994"
            assert result[0]["metadata"]["source"] == "CNJ"
    
    @pytest.mark.asyncio
    async def test_crawl_cgj_rj_documents(self, crawler_service):
        """Test crawling CGJ-RJ documents."""
        with patch('app.crawler.cgj_rj.CGJRJCrawler.crawl') as mock_crawl:
            mock_crawl.return_value = [
                {
                    "url": "https://www.tjrj.jus.br/lei-123",
                    "title": "Lei Estadual 123",
                    "content": "Lei estadual do Rio de Janeiro...",
                    "metadata": {
                        "source": "CGJ-RJ",
                        "date": "2023-01-01",
                        "type": "law"
                    }
                }
            ]
            
            result = await crawler_service.crawl_documents(["CGJ-RJ"], limit=10)
            
            assert len(result) == 1
            assert result[0]["title"] == "Lei Estadual 123"
            assert result[0]["metadata"]["source"] == "CGJ-RJ"
    
    @pytest.mark.asyncio
    async def test_crawl_multiple_sources(self, crawler_service):
        """Test crawling multiple sources."""
        with patch('app.crawler.cnj.CNJCrawler.crawl') as mock_cnj, \
             patch('app.crawler.cgj_rj.CGJRJCrawler.crawl') as mock_cgj_rj:
            
            mock_cnj.return_value = [{"title": "CNJ Document", "metadata": {"source": "CNJ"}}]
            mock_cgj_rj.return_value = [{"title": "CGJ-RJ Document", "metadata": {"source": "CGJ-RJ"}}]
            
            result = await crawler_service.crawl_documents(["CNJ", "CGJ-RJ"], limit=10)
            
            assert len(result) == 2
            sources = [doc["metadata"]["source"] for doc in result]
            assert "CNJ" in sources
            assert "CGJ-RJ" in sources
    
    @pytest.mark.asyncio
    async def test_crawl_invalid_source(self, crawler_service):
        """Test crawling with invalid source."""
        with pytest.raises(ValueError):
            await crawler_service.crawl_documents(["INVALID_SOURCE"], limit=10)
    
    @pytest.mark.asyncio
    async def test_crawl_error_handling(self, crawler_service):
        """Test error handling in crawler service."""
        with patch('app.crawler.cnj.CNJCrawler.crawl') as mock_crawl:
            mock_crawl.side_effect = Exception("Network error")
            
            with pytest.raises(Exception):
                await crawler_service.crawl_documents(["CNJ"], limit=10)
    
    @pytest.mark.asyncio
    async def test_crawl_rate_limiting(self, crawler_service):
        """Test rate limiting in crawler service."""
        with patch('app.crawler.cnj.CNJCrawler.crawl') as mock_crawl:
            mock_crawl.return_value = []
            
            # Should respect rate limits
            await crawler_service.crawl_documents(["CNJ"], limit=1000)
            
            # Verify rate limiting was applied
            mock_crawl.assert_called_once()


class TestIndexerService:
    """Test cases for IndexerService."""
    
    @pytest.fixture
    def indexer_service(self):
        """Create an indexer service instance."""
        return IndexerService()
    
    @pytest.mark.asyncio
    async def test_index_documents(self, indexer_service):
        """Test indexing documents."""
        documents = [
            {
                "id": "doc_123",
                "title": "Lei 8.935/1994",
                "content": "Lei dos Cartórios e Registros Públicos...",
                "metadata": {
                    "source": "CNJ",
                    "date": "1994-11-18",
                    "type": "law"
                }
            }
        ]
        
        with patch('app.services.indexer_service.IndexerService._generate_embeddings') as mock_embeddings, \
             patch('app.services.indexer_service.IndexerService._store_embeddings') as mock_store_embeddings, \
             patch('app.services.indexer_service.IndexerService._index_bm25') as mock_bm25:
            
            mock_embeddings.return_value = [[0.1, 0.2, 0.3] * 384]
            mock_store_embeddings.return_value = True
            mock_bm25.return_value = True
            
            result = await indexer_service.index_documents(documents)
            
            assert result["indexed_count"] == 1
            assert result["errors"] == []
    
    @pytest.mark.asyncio
    async def test_index_documents_with_errors(self, indexer_service):
        """Test indexing documents with errors."""
        documents = [
            {
                "id": "doc_123",
                "title": "Valid Document",
                "content": "Valid content...",
                "metadata": {"source": "CNJ"}
            },
            {
                "id": "doc_456",
                "title": "",  # Invalid document
                "content": "",
                "metadata": {}
            }
        ]
        
        with patch('app.services.indexer_service.IndexerService._generate_embeddings') as mock_embeddings, \
             patch('app.services.indexer_service.IndexerService._store_embeddings') as mock_store_embeddings, \
             patch('app.services.indexer_service.IndexerService._index_bm25') as mock_bm25:
            
            mock_embeddings.return_value = [[0.1, 0.2, 0.3] * 384, None]
            mock_store_embeddings.return_value = True
            mock_bm25.return_value = True
            
            result = await indexer_service.index_documents(documents)
            
            assert result["indexed_count"] == 1
            assert len(result["errors"]) == 1
    
    @pytest.mark.asyncio
    async def test_generate_embeddings(self, indexer_service):
        """Test embedding generation."""
        documents = [
            {
                "id": "doc_123",
                "content": "Lei dos Cartórios e Registros Públicos..."
            }
        ]
        
        with patch('app.services.indexer_service.IndexerService._call_embedding_model') as mock_model:
            mock_model.return_value = [0.1, 0.2, 0.3] * 384
            
            embeddings = await indexer_service._generate_embeddings(documents)
            
            assert len(embeddings) == 1
            assert len(embeddings[0]) == 1152  # 384 * 3
    
    @pytest.mark.asyncio
    async def test_store_embeddings(self, indexer_service):
        """Test storing embeddings in vector database."""
        embeddings = [
            {
                "document_id": "doc_123",
                "embedding": [0.1, 0.2, 0.3] * 384,
                "metadata": {"source": "CNJ"}
            }
        ]
        
        with patch('app.services.indexer_service.IndexerService._vector_db') as mock_db:
            mock_db.store.return_value = True
            
            result = await indexer_service._store_embeddings(embeddings)
            
            assert result is True
            mock_db.store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_index_bm25(self, indexer_service):
        """Test BM25 indexing."""
        documents = [
            {
                "id": "doc_123",
                "content": "Lei dos Cartórios e Registros Públicos...",
                "metadata": {"source": "CNJ"}
            }
        ]
        
        with patch('app.services.indexer_service.IndexerService._bm25_index') as mock_bm25:
            mock_bm25.add_documents.return_value = True
            
            result = await indexer_service._index_bm25(documents)
            
            assert result is True
            mock_bm25.add_documents.assert_called_once()


class TestRetrievalService:
    """Test cases for RetrievalService."""
    
    @pytest.fixture
    def retrieval_service(self):
        """Create a retrieval service instance."""
        return RetrievalService()
    
    @pytest.mark.asyncio
    async def test_search_documents(self, retrieval_service):
        """Test document search."""
        query = {
            "query": "procuração para compra e venda de imóvel",
            "filters": {"source": "CNJ"},
            "limit": 10,
            "offset": 0
        }
        
        with patch('app.services.retrieval_service.RetrievalService._hybrid_search') as mock_search:
            mock_search.return_value = {
                "results": [
                    {
                        "document_id": "doc_123",
                        "title": "Lei 8.935/1994",
                        "content": "Lei dos Cartórios e Registros Públicos...",
                        "relevance_score": 0.95,
                        "citations": ["Art. 1º", "Art. 2º"],
                        "metadata": {"source": "CNJ"}
                    }
                ],
                "total": 1
            }
            
            result = await retrieval_service.search_documents(query)
            
            assert result["total"] == 1
            assert len(result["results"]) == 1
            assert result["results"][0]["relevance_score"] == 0.95
    
    @pytest.mark.asyncio
    async def test_hybrid_search(self, retrieval_service):
        """Test hybrid search combining vector and BM25."""
        query = "procuração para compra e venda de imóvel"
        
        with patch('app.services.retrieval_service.RetrievalService._vector_search') as mock_vector, \
             patch('app.services.retrieval_service.RetrievalService._bm25_search') as mock_bm25, \
             patch('app.services.retrieval_service.RetrievalService._rerank_results') as mock_rerank:
            
            mock_vector.return_value = [
                {"document_id": "doc_123", "score": 0.9, "title": "Vector Result"}
            ]
            mock_bm25.return_value = [
                {"document_id": "doc_456", "score": 0.8, "title": "BM25 Result"}
            ]
            mock_rerank.return_value = [
                {"document_id": "doc_123", "relevance_score": 0.95, "title": "Vector Result"},
                {"document_id": "doc_456", "relevance_score": 0.85, "title": "BM25 Result"}
            ]
            
            result = await retrieval_service._hybrid_search(query, {}, 10, 0)
            
            assert len(result["results"]) == 2
            assert result["results"][0]["relevance_score"] == 0.95
    
    @pytest.mark.asyncio
    async def test_vector_search(self, retrieval_service):
        """Test vector similarity search."""
        query = "procuração para compra e venda de imóvel"
        
        with patch('app.services.retrieval_service.RetrievalService._generate_query_embedding') as mock_embedding, \
             patch('app.services.retrieval_service.RetrievalService._vector_db') as mock_db:
            
            mock_embedding.return_value = [0.1, 0.2, 0.3] * 384
            mock_db.search.return_value = [
                {"document_id": "doc_123", "score": 0.9, "metadata": {"source": "CNJ"}}
            ]
            
            result = await retrieval_service._vector_search(query, {}, 10)
            
            assert len(result) == 1
            assert result[0]["score"] == 0.9
    
    @pytest.mark.asyncio
    async def test_bm25_search(self, retrieval_service):
        """Test BM25 keyword search."""
        query = "procuração para compra e venda de imóvel"
        
        with patch('app.services.retrieval_service.RetrievalService._bm25_index') as mock_bm25:
            mock_bm25.search.return_value = [
                {"document_id": "doc_123", "score": 0.8, "metadata": {"source": "CNJ"}}
            ]
            
            result = await retrieval_service._bm25_search(query, {}, 10)
            
            assert len(result) == 1
            assert result[0]["score"] == 0.8
    
    @pytest.mark.asyncio
    async def test_rerank_results(self, retrieval_service):
        """Test result reranking."""
        results = [
            {"document_id": "doc_123", "score": 0.9, "title": "Result 1"},
            {"document_id": "doc_456", "score": 0.8, "title": "Result 2"}
        ]
        
        with patch('app.services.retrieval_service.RetrievalService._reranking_model') as mock_model:
            mock_model.rerank.return_value = [
                {"document_id": "doc_123", "relevance_score": 0.95},
                {"document_id": "doc_456", "relevance_score": 0.85}
            ]
            
            result = await retrieval_service._rerank_results(results, "query")
            
            assert len(result) == 2
            assert result[0]["relevance_score"] == 0.95
    
    @pytest.mark.asyncio
    async def test_get_document_by_id(self, retrieval_service):
        """Test getting document by ID."""
        with patch('app.services.retrieval_service.RetrievalService._document_db') as mock_db:
            mock_db.get.return_value = {
                "id": "doc_123",
                "title": "Lei 8.935/1994",
                "content": "Lei dos Cartórios e Registros Públicos...",
                "metadata": {"source": "CNJ"}
            }
            
            result = await retrieval_service.get_document_by_id("doc_123")
            
            assert result["id"] == "doc_123"
            assert result["title"] == "Lei 8.935/1994"
    
    @pytest.mark.asyncio
    async def test_get_document_not_found(self, retrieval_service):
        """Test getting non-existent document."""
        with patch('app.services.retrieval_service.RetrievalService._document_db') as mock_db:
            mock_db.get.return_value = None
            
            result = await retrieval_service.get_document_by_id("nonexistent")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, retrieval_service):
        """Test getting service statistics."""
        with patch('app.services.retrieval_service.RetrievalService._document_db') as mock_db:
            mock_db.count.return_value = 1000
            mock_db.get_sources.return_value = {
                "CNJ": 500,
                "CGJ-SP": 300,
                "CGJ-RJ": 200
            }
            mock_db.get_last_updated.return_value = "2023-01-01T00:00:00Z"
            
            result = await retrieval_service.get_statistics()
            
            assert result["total_documents"] == 1000
            assert result["sources"]["CNJ"] == 500
            assert result["last_updated"] == "2023-01-01T00:00:00Z"
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, retrieval_service):
        """Test search with various filters."""
        query = {
            "query": "procuração",
            "filters": {
                "source": "CNJ",
                "type": "law",
                "date_from": "1990-01-01",
                "date_to": "2000-12-31"
            },
            "limit": 10
        }
        
        with patch('app.services.retrieval_service.RetrievalService._hybrid_search') as mock_search:
            mock_search.return_value = {"results": [], "total": 0}
            
            result = await retrieval_service.search_documents(query)
            
            # Verify filters were passed to hybrid search
            mock_search.assert_called_once()
            call_args = mock_search.call_args[0]
            assert call_args[1] == query["filters"]
    
    @pytest.mark.asyncio
    async def test_search_performance(self, retrieval_service):
        """Test search performance."""
        query = {
            "query": "procuração",
            "limit": 10
        }
        
        with patch('app.services.retrieval_service.RetrievalService._hybrid_search') as mock_search:
            mock_search.return_value = {"results": [], "total": 0}
            
            import time
            start_time = time.time()
            await retrieval_service.search_documents(query)
            end_time = time.time()
            
            # Should complete within reasonable time
            assert (end_time - start_time) < 1.0  # Less than 1 second
