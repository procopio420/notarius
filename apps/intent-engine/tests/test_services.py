"""
Tests for Intent Engine services.
"""
import pytest
from unittest.mock import patch, MagicMock
from app.services.intent_service import IntentService
from app.services.draft_service import DraftService
from app.services.pii_service import PIIService
from app.services.legal_service import LegalService


class TestIntentService:
    """Test cases for Intent Service."""
    
    @pytest.fixture
    def intent_service(self):
        """Create an Intent Service instance."""
        return IntentService()
    
    def test_parse_intent_success(self, intent_service):
        """Test successful intent parsing."""
        with patch('app.services.intent_service.openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': '{"action": "create", "document_type": "procuracao", "entities": {"outorgante": "João Silva", "outorgado": "Maria Santos"}}'
                    }
                }]
            }
            
            result = intent_service.parse_intent(
                intent="Criar uma procuração para João Silva representar Maria Santos",
                processo_id="proc_123",
                tenant_id="tenant_456",
                user_id="user_789"
            )
            
            assert result["action"] == "create"
            assert result["document_type"] == "procuracao"
            assert result["entities"]["outorgante"] == "João Silva"
            assert result["entities"]["outorgado"] == "Maria Santos"
    
    def test_parse_intent_invalid_json(self, intent_service):
        """Test intent parsing with invalid JSON response."""
        with patch('app.services.intent_service.openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': 'Invalid JSON response'
                    }
                }]
            }
            
            with pytest.raises(ValueError):
                intent_service.parse_intent(
                    intent="Criar uma procuração",
                    processo_id="proc_123",
                    tenant_id="tenant_456",
                    user_id="user_789"
                )
    
    def test_parse_intent_openai_error(self, intent_service):
        """Test intent parsing with OpenAI API error."""
        with patch('app.services.intent_service.openai.ChatCompletion.create') as mock_openai:
            mock_openai.side_effect = Exception("OpenAI API error")
            
            with pytest.raises(Exception):
                intent_service.parse_intent(
                    intent="Criar uma procuração",
                    processo_id="proc_123",
                    tenant_id="tenant_456",
                    user_id="user_789"
                )
    
    def test_validate_intent_valid(self, intent_service):
        """Test intent validation with valid intent."""
        with patch('app.services.intent_service.openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': '{"is_valid": true, "confidence": 0.95, "suggestions": [], "errors": []}'
                    }
                }]
            }
            
            result = intent_service.validate_intent(
                intent="Criar uma procuração para João Silva representar Maria Santos",
                document_type="procuracao"
            )
            
            assert result["is_valid"] is True
            assert result["confidence"] == 0.95
            assert len(result["suggestions"]) == 0
            assert len(result["errors"]) == 0
    
    def test_validate_intent_invalid(self, intent_service):
        """Test intent validation with invalid intent."""
        with patch('app.services.intent_service.openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': '{"is_valid": false, "confidence": 0.2, "suggestions": ["Specify document type"], "errors": ["Intent too vague"]}'
                    }
                }]
            }
            
            result = intent_service.validate_intent(
                intent="Invalid intent",
                document_type="procuracao"
            )
            
            assert result["is_valid"] is False
            assert result["confidence"] == 0.2
            assert len(result["suggestions"]) > 0
            assert len(result["errors"]) > 0
    
    def test_get_supported_document_types(self, intent_service):
        """Test getting supported document types."""
        result = intent_service.get_supported_document_types()
        
        assert "document_types" in result
        assert len(result["document_types"]) > 0
        
        # Check that each document type has required fields
        for doc_type in result["document_types"]:
            assert "type" in doc_type
            assert "name" in doc_type
            assert "description" in doc_type
            assert "supported_actions" in doc_type
    
    def test_get_intent_templates(self, intent_service):
        """Test getting intent templates."""
        result = intent_service.get_intent_templates()
        
        assert "templates" in result
        assert len(result["templates"]) > 0
        
        # Check that each template has required fields
        for template in result["templates"]:
            assert "id" in template
            assert "name" in template
            assert "description" in template
            assert "example" in template
            assert "document_type" in template


class TestDraftService:
    """Test cases for Draft Service."""
    
    @pytest.fixture
    def draft_service(self):
        """Create a Draft Service instance."""
        return DraftService()
    
    def test_generate_draft_success(self, draft_service):
        """Test successful draft generation."""
        with patch('app.services.draft_service.openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': 'PROCURAÇÃO\n\nJoão Silva, CPF 123.456.789-00, nomeia Maria Santos como seu procurador...'
                    }
                }]
            }
            
            with patch('app.services.draft_service.LexNodeClient.get_legal_citations') as mock_citations:
                mock_citations.return_value = {
                    "citations": [
                        {
                            "source": "Lei 8.935/1994",
                            "relevance": 0.95,
                            "excerpt": "Art. 1º - A procuração é o instrumento..."
                        }
                    ]
                }
                
                result = draft_service.generate_draft(
                    intent_id="intent_123",
                    template_id="template_456",
                    processo_id="proc_789",
                    tenant_id="tenant_101",
                    user_id="user_202"
                )
                
                assert "PROCURAÇÃO" in result["content"]
                assert result["grounding_confidence"] > 0.8
                assert len(result["citations"]) > 0
    
    def test_generate_draft_openai_error(self, draft_service):
        """Test draft generation with OpenAI API error."""
        with patch('app.services.draft_service.openai.ChatCompletion.create') as mock_openai:
            mock_openai.side_effect = Exception("OpenAI API error")
            
            with pytest.raises(Exception):
                draft_service.generate_draft(
                    intent_id="intent_123",
                    template_id="template_456",
                    processo_id="proc_789",
                    tenant_id="tenant_101",
                    user_id="user_202"
                )
    
    def test_generate_draft_lexnode_error(self, draft_service):
        """Test draft generation with LexNode service error."""
        with patch('app.services.draft_service.openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': 'PROCURAÇÃO\n\nJoão Silva, CPF 123.456.789-00, nomeia Maria Santos como seu procurador...'
                    }
                }]
            }
            
            with patch('app.services.draft_service.LexNodeClient.get_legal_citations') as mock_citations:
                mock_citations.side_effect = Exception("LexNode service error")
                
                with pytest.raises(Exception):
                    draft_service.generate_draft(
                        intent_id="intent_123",
                        template_id="template_456",
                        processo_id="proc_789",
                        tenant_id="tenant_101",
                        user_id="user_202"
                    )
    
    def test_generate_draft_low_confidence(self, draft_service):
        """Test draft generation with low confidence."""
        with patch('app.services.draft_service.openai.ChatCompletion.create') as mock_openai:
            mock_openai.return_value = {
                'choices': [{
                    'message': {
                        'content': 'PROCURAÇÃO\n\nJoão Silva, CPF 123.456.789-00, nomeia Maria Santos como seu procurador...'
                    }
                }]
            }
            
            with patch('app.services.draft_service.LexNodeClient.get_legal_citations') as mock_citations:
                mock_citations.return_value = {
                    "citations": [
                        {
                            "source": "Lei 8.935/1994",
                            "relevance": 0.3,  # Low relevance
                            "excerpt": "Art. 1º - A procuração é o instrumento..."
                        }
                    ]
                }
                
                result = draft_service.generate_draft(
                    intent_id="intent_123",
                    template_id="template_456",
                    processo_id="proc_789",
                    tenant_id="tenant_101",
                    user_id="user_202"
                )
                
                assert result["grounding_confidence"] < 0.5
                assert "warning" in result or "low_confidence" in result


class TestPIIService:
    """Test cases for PII Service."""
    
    @pytest.fixture
    def pii_service(self):
        """Create a PII Service instance."""
        return PIIService()
    
    def test_extract_pii_success(self, pii_service):
        """Test successful PII extraction."""
        with patch('app.services.pii_service.PIIExtractor.extract') as mock_extract:
            mock_extract.return_value = {
                "nome": ["João Silva"],
                "cpf": ["123.456.789-00"],
                "email": ["joao@email.com"]
            }
            
            result = pii_service.extract_pii(
                text="João Silva, CPF 123.456.789-00, email joao@email.com",
                extraction_types=["nome", "cpf", "email"]
            )
            
            assert "João Silva" in result["extracted_pii"]["nome"]
            assert "123.456.789-00" in result["extracted_pii"]["cpf"]
            assert "joao@email.com" in result["extracted_pii"]["email"]
            assert result["confidence"] > 0.8
    
    def test_extract_pii_no_pii_found(self, pii_service):
        """Test PII extraction with no PII found."""
        with patch('app.services.pii_service.PIIExtractor.extract') as mock_extract:
            mock_extract.return_value = {}
            
            result = pii_service.extract_pii(
                text="This is a normal text with no PII",
                extraction_types=["nome", "cpf", "email"]
            )
            
            assert len(result["extracted_pii"]) == 0
            assert result["confidence"] == 0.0
    
    def test_extract_pii_partial_match(self, pii_service):
        """Test PII extraction with partial matches."""
        with patch('app.services.pii_service.PIIExtractor.extract') as mock_extract:
            mock_extract.return_value = {
                "nome": ["João Silva"],
                "cpf": []  # No CPF found
            }
            
            result = pii_service.extract_pii(
                text="João Silva, residente no Rio de Janeiro",
                extraction_types=["nome", "cpf"]
            )
            
            assert "João Silva" in result["extracted_pii"]["nome"]
            assert len(result["extracted_pii"]["cpf"]) == 0
            assert result["confidence"] < 1.0
    
    def test_extract_pii_invalid_types(self, pii_service):
        """Test PII extraction with invalid extraction types."""
        with pytest.raises(ValueError):
            pii_service.extract_pii(
                text="João Silva, CPF 123.456.789-00",
                extraction_types=["invalid_type"]
            )
    
    def test_extract_pii_empty_text(self, pii_service):
        """Test PII extraction with empty text."""
        with pytest.raises(ValueError):
            pii_service.extract_pii(
                text="",
                extraction_types=["nome", "cpf"]
            )
    
    def test_extract_pii_none_text(self, pii_service):
        """Test PII extraction with None text."""
        with pytest.raises(ValueError):
            pii_service.extract_pii(
                text=None,
                extraction_types=["nome", "cpf"]
            )


class TestLegalService:
    """Test cases for Legal Service."""
    
    @pytest.fixture
    def legal_service(self):
        """Create a Legal Service instance."""
        return LegalService()
    
    def test_get_citations_success(self, legal_service):
        """Test successful legal citation retrieval."""
        with patch('app.services.legal_service.LexNodeClient.get_legal_citations') as mock_citations:
            mock_citations.return_value = {
                "citations": [
                    {
                        "source": "Lei 8.935/1994",
                        "relevance": 0.95,
                        "excerpt": "Art. 1º - A procuração é o instrumento...",
                        "url": "https://example.com/lei-8935-1994"
                    },
                    {
                        "source": "Código Civil",
                        "relevance": 0.88,
                        "excerpt": "Art. 653 - A procuração pode ser...",
                        "url": "https://example.com/codigo-civil"
                    }
                ]
            }
            
            result = legal_service.get_citations(
                intent="Criar uma procuração para João Silva representar Maria Santos",
                jurisdiction="RJ"
            )
            
            assert result["total"] == 2
            assert len(result["citations"]) == 2
            assert result["citations"][0]["source"] == "Lei 8.935/1994"
            assert result["citations"][0]["relevance"] == 0.95
    
    def test_get_citations_no_results(self, legal_service):
        """Test legal citation retrieval with no results."""
        with patch('app.services.legal_service.LexNodeClient.get_legal_citations') as mock_citations:
            mock_citations.return_value = {
                "citations": []
            }
            
            result = legal_service.get_citations(
                intent="Invalid intent that doesn't match any legal concepts",
                jurisdiction="RJ"
            )
            
            assert result["total"] == 0
            assert len(result["citations"]) == 0
    
    def test_get_citations_lexnode_error(self, legal_service):
        """Test legal citation retrieval with LexNode service error."""
        with patch('app.services.legal_service.LexNodeClient.get_legal_citations') as mock_citations:
            mock_citations.side_effect = Exception("LexNode service error")
            
            with pytest.raises(Exception):
                legal_service.get_citations(
                    intent="Criar uma procuração",
                    jurisdiction="RJ"
                )
    
    def test_get_citations_invalid_jurisdiction(self, legal_service):
        """Test legal citation retrieval with invalid jurisdiction."""
        with pytest.raises(ValueError):
            legal_service.get_citations(
                intent="Criar uma procuração",
                jurisdiction="INVALID"
            )
    
    def test_get_citations_empty_intent(self, legal_service):
        """Test legal citation retrieval with empty intent."""
        with pytest.raises(ValueError):
            legal_service.get_citations(
                intent="",
                jurisdiction="RJ"
            )
    
    def test_get_citations_none_intent(self, legal_service):
        """Test legal citation retrieval with None intent."""
        with pytest.raises(ValueError):
            legal_service.get_citations(
                intent=None,
                jurisdiction="RJ"
            )
