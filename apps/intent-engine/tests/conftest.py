"""
Pytest configuration for Intent Engine tests.
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
def mock_intent_request():
    """Mock intent request for testing."""
    return {
        "intent": "Criar uma procuração para João Silva representar Maria Santos em uma compra e venda de imóvel",
        "processo_id": "proc_123",
        "tenant_id": "tenant_456",
        "user_id": "user_789"
    }


@pytest.fixture
def mock_intent_response():
    """Mock intent response for testing."""
    return {
        "intent_id": "intent_123",
        "parsed_intent": {
            "action": "create",
            "document_type": "procuracao",
            "parties": [
                {
                    "role": "outorgante",
                    "name": "João Silva",
                    "type": "pf"
                },
                {
                    "role": "outorgado",
                    "name": "Maria Santos",
                    "type": "pf"
                }
            ],
            "subject": "compra e venda de imóvel",
            "jurisdiction": "RJ"
        },
        "pii_extracted": {
            "nome_outorgante": "João Silva",
            "nome_outorgado": "Maria Santos"
        },
        "legal_citations": [
            {
                "source": "Lei 8.935/1994",
                "article": "Art. 1º",
                "relevance": 0.95
            },
            {
                "source": "Código Civil",
                "article": "Art. 1.123",
                "relevance": 0.87
            }
        ],
        "confidence": 0.92,
        "status": "success"
    }


@pytest.fixture
def mock_draft_request():
    """Mock draft generation request for testing."""
    return {
        "intent_id": "intent_123",
        "template_id": "template_456",
        "pii_tokens": {
            "nome_outorgante": "token_12345678-1234-1234-1234-123456789012",
            "nome_outorgado": "token_87654321-4321-4321-4321-210987654321"
        },
        "legal_citations": [
            {
                "source": "Lei 8.935/1994",
                "article": "Art. 1º",
                "relevance": 0.95
            }
        ]
    }


@pytest.fixture
def mock_draft_response():
    """Mock draft generation response for testing."""
    return {
        "draft_id": "draft_123",
        "content": "# PROCURAÇÃO\n\n**Outorgante:** {{nome_outorgante}}\n**Outorgado:** {{nome_outorgado}}\n\nPelo presente instrumento particular de procuração...",
        "variables": {
            "nome_outorgante": "token_12345678-1234-1234-1234-123456789012",
            "nome_outorgado": "token_87654321-4321-4321-4321-210987654321"
        },
        "citations": [
            {
                "source": "Lei 8.935/1994",
                "article": "Art. 1º",
                "relevance": 0.95
            }
        ],
        "grounding_confidence": 0.92,
        "status": "success"
    }


@pytest.fixture
def mock_pii_extraction_request():
    """Mock PII extraction request for testing."""
    return {
        "text": "João Silva, CPF 123.456.789-00, residente na Rua das Flores, 123, Centro, Rio de Janeiro - RJ, telefone (21) 99999-9999, email joao.silva@email.com",
        "extraction_types": ["nome", "cpf", "endereco", "telefone", "email"]
    }


@pytest.fixture
def mock_pii_extraction_response():
    """Mock PII extraction response for testing."""
    return {
        "extracted_pii": {
            "nome": ["João Silva"],
            "cpf": ["123.456.789-00"],
            "endereco": ["Rua das Flores, 123, Centro, Rio de Janeiro - RJ"],
            "telefone": ["(21) 99999-9999"],
            "email": ["joao.silva@email.com"]
        },
        "tokens": {
            "nome": "token_12345678-1234-1234-1234-123456789012",
            "cpf": "token_87654321-4321-4321-4321-210987654321",
            "endereco": "token_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "telefone": "token_ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj",
            "email": "token_kkkkkkkk-llll-mmmm-nnnn-oooooooooooo"
        },
        "confidence": 0.95,
        "status": "success"
    }


@pytest.fixture
def mock_legal_citation_request():
    """Mock legal citation request for testing."""
    return {
        "intent": "procuração para compra e venda de imóvel",
        "jurisdiction": "RJ",
        "document_type": "procuracao"
    }


@pytest.fixture
def mock_legal_citation_response():
    """Mock legal citation response for testing."""
    return {
        "citations": [
            {
                "source": "Lei 8.935/1994",
                "article": "Art. 1º",
                "content": "Lei dos Cartórios e Registros Públicos...",
                "relevance": 0.95,
                "jurisdiction": "federal"
            },
            {
                "source": "Código Civil",
                "article": "Art. 1.123",
                "content": "Do contrato de compra e venda...",
                "relevance": 0.87,
                "jurisdiction": "federal"
            }
        ],
        "total": 2,
        "confidence": 0.91,
        "status": "success"
    }
