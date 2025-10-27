"""
Pytest configuration for integration and E2E tests.
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from django.test import Client as DjangoClient
from unittest.mock import patch, MagicMock


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def notarius_client():
    """Create a Django test client for Notarius API."""
    return DjangoClient()


@pytest.fixture
def lexnode_client():
    """Create a FastAPI test client for LexNode API."""
    from apps.lexnode.main import app
    return TestClient(app)


@pytest.fixture
def intent_engine_client():
    """Create a FastAPI test client for Intent Engine API."""
    from apps.intent_engine.main import app
    return TestClient(app)


@pytest.fixture
def pii_vault_client():
    """Create a FastAPI test client for PII Vault API."""
    from apps.pii_vault.main import app
    return TestClient(app)


@pytest.fixture
def mock_services():
    """Mock external services for testing."""
    with patch('apps.lexnode.services.crawler.CrawlerService') as mock_crawler, \
         patch('apps.lexnode.services.normalizer.NormalizerService') as mock_normalizer, \
         patch('apps.lexnode.services.indexer.IndexerService') as mock_indexer, \
         patch('apps.lexnode.services.retrieval.RetrievalService') as mock_retrieval, \
         patch('apps.intent_engine.services.intent_service.IntentService') as mock_intent, \
         patch('apps.intent_engine.services.draft_service.DraftService') as mock_draft, \
         patch('apps.intent_engine.services.pii_service.PIIService') as mock_pii, \
         patch('apps.intent_engine.services.legal_service.LegalService') as mock_legal, \
         patch('apps.pii_vault.services.vault.PIIVaultService') as mock_vault, \
         patch('apps.pii_vault.services.tokenizer.TokenizerService') as mock_tokenizer:
        
        # Configure mock responses
        mock_crawler.return_value.crawl.return_value = {
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
        
        mock_normalizer.return_value.normalize.return_value = {
            "status": "success",
            "normalized_documents": [
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
            ]
        }
        
        mock_indexer.return_value.index.return_value = {
            "status": "success",
            "indexed_count": 1
        }
        
        mock_retrieval.return_value.retrieve.return_value = {
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
        
        mock_intent.return_value.parse_intent.return_value = {
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
        
        mock_draft.return_value.generate_draft.return_value = {
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
        
        mock_pii.return_value.extract_pii.return_value = {
            "extracted_pii": {
                "nome": ["João Silva"],
                "cpf": ["123.456.789-00"]
            },
            "confidence": 0.95
        }
        
        mock_legal.return_value.get_citations.return_value = {
            "total": 1,
            "citations": [
                {
                    "source": "Lei 8.935/1994",
                    "relevance": 0.95,
                    "excerpt": "Art. 1º - A procuração é o instrumento..."
                }
            ]
        }
        
        mock_vault.return_value.store_pii.return_value = {
            "status": "success",
            "pii_id": "pii_123"
        }
        
        mock_tokenizer.return_value.tokenize.return_value = {
            "status": "success",
            "tokens": {
                "nome": "TOKEN_NOME_123",
                "cpf": "TOKEN_CPF_456"
            }
        }
        
        yield {
            "crawler": mock_crawler,
            "normalizer": mock_normalizer,
            "indexer": mock_indexer,
            "retrieval": mock_retrieval,
            "intent": mock_intent,
            "draft": mock_draft,
            "pii": mock_pii,
            "legal": mock_legal,
            "vault": mock_vault,
            "tokenizer": mock_tokenizer
        }


@pytest.fixture
def test_tenant():
    """Create a test tenant."""
    return {
        "id": "tenant_123",
        "name": "Cartório Teste",
        "jurisdiction": "RJ",
        "settings": {
            "document_types": ["procuracao", "certidao"],
            "ai_enabled": True
        }
    }


@pytest.fixture
def test_processo():
    """Create a test processo."""
    return {
        "id": "proc_123",
        "tenant_id": "tenant_123",
        "numero": "2024.001.000001",
        "tipo": "procuracao",
        "status": "draft"
    }


@pytest.fixture
def test_intent():
    """Create a test intent."""
    return {
        "intent": "Criar uma procuração para João Silva representar Maria Santos em uma compra e venda de imóvel",
        "processo_id": "proc_123",
        "tenant_id": "tenant_123",
        "user_id": "user_456"
    }


@pytest.fixture
def test_draft():
    """Create a test draft."""
    return {
        "intent_id": "intent_123",
        "template_id": "template_456",
        "processo_id": "proc_123",
        "tenant_id": "tenant_123",
        "user_id": "user_456"
    }


@pytest.fixture
def test_pii_extraction():
    """Create a test PII extraction request."""
    return {
        "text": "João Silva, CPF 123.456.789-00, residente na Rua das Flores, 123",
        "extraction_types": ["nome", "cpf", "endereco"]
    }


@pytest.fixture
def test_legal_citation():
    """Create a test legal citation request."""
    return {
        "intent": "Criar uma procuração para João Silva representar Maria Santos",
        "jurisdiction": "RJ"
    }
