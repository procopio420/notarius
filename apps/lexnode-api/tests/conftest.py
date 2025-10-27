"""
Pytest configuration for LexNode API tests.
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_document_data():
    """Mock document data for testing."""
    return {
        "id": "doc_123",
        "title": "Lei 8.935/1994",
        "content": "Lei dos Cartórios e Registros Públicos...",
        "source": "CNJ",
        "url": "https://www.cnj.jus.br/lei-8935-1994/",
        "metadata": {
            "date": "1994-11-18",
            "type": "law",
            "jurisdiction": "federal"
        },
        "embeddings": [0.1, 0.2, 0.3] * 384,  # Mock 1152-dimensional embedding
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_search_query():
    """Mock search query for testing."""
    return {
        "query": "procuração para compra e venda de imóvel",
        "filters": {
            "source": "CNJ",
            "type": "law",
            "jurisdiction": "federal"
        },
        "limit": 10,
        "offset": 0
    }


@pytest.fixture
def mock_search_results():
    """Mock search results for testing."""
    return {
        "results": [
            {
                "id": "doc_123",
                "title": "Lei 8.935/1994",
                "content": "Lei dos Cartórios e Registros Públicos...",
                "source": "CNJ",
                "relevance_score": 0.95,
                "citations": ["Art. 1º", "Art. 2º"],
                "metadata": {
                    "date": "1994-11-18",
                    "type": "law",
                    "jurisdiction": "federal"
                }
            },
            {
                "id": "doc_456",
                "title": "Código Civil - Art. 1.123",
                "content": "Do contrato de compra e venda...",
                "source": "CGJ-SP",
                "relevance_score": 0.87,
                "citations": ["Art. 1.123", "Art. 1.124"],
                "metadata": {
                    "date": "2002-01-10",
                    "type": "law",
                    "jurisdiction": "federal"
                }
            }
        ],
        "total": 2,
        "query": "procuração para compra e venda de imóvel",
        "filters": {
            "source": "CNJ",
            "type": "law",
            "jurisdiction": "federal"
        },
        "limit": 10,
        "offset": 0
    }


@pytest.fixture
def mock_crawler_data():
    """Mock crawler data for testing."""
    return {
        "url": "https://www.cnj.jus.br/lei-8935-1994/",
        "title": "Lei 8.935/1994",
        "content": "Lei dos Cartórios e Registros Públicos...",
        "metadata": {
            "source": "CNJ",
            "date": "1994-11-18",
            "type": "law",
            "jurisdiction": "federal"
        }
    }


@pytest.fixture
def mock_indexer_data():
    """Mock indexer data for testing."""
    return {
        "document_id": "doc_123",
        "title": "Lei 8.935/1994",
        "content": "Lei dos Cartórios e Registros Públicos...",
        "embeddings": [0.1, 0.2, 0.3] * 384,
        "bm25_tokens": ["lei", "cartórios", "registros", "públicos"],
        "metadata": {
            "source": "CNJ",
            "date": "1994-11-18",
            "type": "law",
            "jurisdiction": "federal"
        }
    }


@pytest.fixture
def mock_retrieval_data():
    """Mock retrieval data for testing."""
    return {
        "query": "procuração para compra e venda de imóvel",
        "hybrid_results": [
            {
                "document_id": "doc_123",
                "title": "Lei 8.935/1994",
                "content": "Lei dos Cartórios e Registros Públicos...",
                "relevance_score": 0.95,
                "citations": ["Art. 1º", "Art. 2º"],
                "metadata": {
                    "source": "CNJ",
                    "date": "1994-11-18",
                    "type": "law",
                    "jurisdiction": "federal"
                }
            }
        ],
        "total": 1,
        "search_time_ms": 150
    }
