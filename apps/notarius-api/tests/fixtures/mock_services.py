"""
Mock services for testing AI and external service integrations.
"""
import asyncio
import json
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

from apps.ai.clients import get_ai_service_manager


class MockAIServiceManager:
    """Mock AI service manager for testing."""
    
    def __init__(self):
        self.mock_responses = {}
        self.call_history = []
    
    def set_mock_response(self, method: str, response: Any):
        """Set mock response for a specific method."""
        self.mock_responses[method] = response
    
    def get_call_history(self, method: str = None) -> List[Dict]:
        """Get call history for a method or all methods."""
        if method:
            return [call for call in self.call_history if call['method'] == method]
        return self.call_history
    
    def clear_call_history(self):
        """Clear call history."""
        self.call_history = []
    
    async def generate_minuta_from_intent(
        self, 
        tenant_id: str, 
        user_id: int, 
        intent: str, 
        processo_id: str
    ) -> Dict[str, Any]:
        """Mock minuta generation from intent."""
        self.call_history.append({
            'method': 'generate_minuta_from_intent',
            'tenant_id': tenant_id,
            'user_id': user_id,
            'intent': intent,
            'processo_id': processo_id
        })
        
        if 'generate_minuta_from_intent' in self.mock_responses:
            return self.mock_responses['generate_minuta_from_intent']
        
        # Default mock response
        return {
            'id': 'mock-minuta-id',
            'corpo_md': f'# Minuta Gerada\n\nBaseado no intent: {intent}',
            'variaveis_json': {
                'nome_outorgante': 'token_12345678-1234-1234-1234-123456789012',
                'nome_outorgado': 'token_87654321-4321-4321-4321-210987654321',
                'endereco': 'token_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
            },
            'citations': [
                {'source': 'Lei 8.935/1994', 'article': 'Art. 1º'},
                {'source': 'Código Civil', 'article': 'Art. 1.123'}
            ],
            'grounding_confidence': 0.85,
            'status': 'rascunho'
        }
    
    async def finalize_minuta(self, minuta, tenant_id: str) -> Dict[str, Any]:
        """Mock minuta finalization."""
        self.call_history.append({
            'method': 'finalize_minuta',
            'minuta_id': str(minuta.id),
            'tenant_id': tenant_id
        })
        
        if 'finalize_minuta' in self.mock_responses:
            return self.mock_responses['finalize_minuta']
        
        # Default mock response
        return {
            'id': 'mock-documento-id',
            's3_key': f'documents/{minuta.id}/final.pdf',
            'hash_sha256': b'mock_hash_32_bytes_long_here',
            'mime': 'application/pdf',
            'pages': 3,
            'status': 'pronto'
        }


class MockPIIService:
    """Mock PII service for testing."""
    
    def __init__(self):
        self.tokens = {}
        self.call_history = []
    
    def tokenize(self, pii_data: Dict[str, str]) -> Dict[str, str]:
        """Mock PII tokenization."""
        self.call_history.append({
            'method': 'tokenize',
            'pii_data': pii_data
        })
        
        tokens = {}
        for field, value in pii_data.items():
            token = f"token_{field}_{hash(value) % 1000000}"
            tokens[field] = token
            self.tokens[token] = value
        
        return tokens
    
    def detokenize(self, tokens: Dict[str, str]) -> Dict[str, str]:
        """Mock PII detokenization."""
        self.call_history.append({
            'method': 'detokenize',
            'tokens': tokens
        })
        
        pii_data = {}
        for field, token in tokens.items():
            pii_data[field] = self.tokens.get(token, f"detokenized_{field}")
        
        return pii_data
    
    def extract_pii(self, text: str) -> Dict[str, List[str]]:
        """Mock PII extraction from text."""
        self.call_history.append({
            'method': 'extract_pii',
            'text': text
        })
        
        # Simple mock extraction
        extracted = {}
        if 'João' in text or 'Silva' in text:
            extracted['nome'] = ['João Silva Santos']
        if '123.456.789' in text:
            extracted['cpf'] = ['123.456.789-00']
        if '12.345.678' in text:
            extracted['cnpj'] = ['12.345.678/0001-90']
        if '@' in text:
            extracted['email'] = ['joao.silva@email.com']
        
        return extracted


class MockLexNodeService:
    """Mock LexNode service for testing."""
    
    def __init__(self):
        self.documents = []
        self.call_history = []
    
    async def search_legal_documents(
        self, 
        query: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Mock legal document search."""
        self.call_history.append({
            'method': 'search_legal_documents',
            'query': query,
            'limit': limit
        })
        
        # Mock search results
        return [
            {
                'id': 'doc_1',
                'title': 'Lei 8.935/1994',
                'content': 'Lei dos Cartórios e Registros Públicos...',
                'source': 'CNJ',
                'relevance_score': 0.95,
                'citations': ['Art. 1º', 'Art. 2º']
            },
            {
                'id': 'doc_2',
                'title': 'Código Civil - Art. 1.123',
                'content': 'Do contrato de compra e venda...',
                'source': 'CGJ-SP',
                'relevance_score': 0.87,
                'citations': ['Art. 1.123', 'Art. 1.124']
            }
        ]
    
    async def get_document_by_id(self, doc_id: str) -> Dict[str, Any]:
        """Mock get document by ID."""
        self.call_history.append({
            'method': 'get_document_by_id',
            'doc_id': doc_id
        })
        
        return {
            'id': doc_id,
            'title': f'Document {doc_id}',
            'content': f'Full content of document {doc_id}...',
            'source': 'CNJ',
            'metadata': {
                'date': '2023-01-01',
                'type': 'law'
            }
        }


class MockStorageService:
    """Mock storage service for testing."""
    
    def __init__(self):
        self.files = {}
        self.call_history = []
    
    def upload_file(
        self, 
        file_obj, 
        tenant_id: str, 
        processo_id: str, 
        filename: str, 
        content_type: str
    ) -> tuple[str, bytes]:
        """Mock file upload."""
        self.call_history.append({
            'method': 'upload_file',
            'tenant_id': tenant_id,
            'processo_id': processo_id,
            'filename': filename,
            'content_type': content_type
        })
        
        s3_key = f"{tenant_id}/{processo_id}/{filename}"
        file_hash = b"mock_hash_32_bytes_long_here"
        
        self.files[s3_key] = {
            'content': file_obj.read() if hasattr(file_obj, 'read') else b'mock_content',
            'content_type': content_type,
            'size': len(file_obj.read()) if hasattr(file_obj, 'read') else 1024
        }
        
        return s3_key, file_hash
    
    def download_file(self, s3_key: str) -> bytes:
        """Mock file download."""
        self.call_history.append({
            'method': 'download_file',
            's3_key': s3_key
        })
        
        if s3_key in self.files:
            return self.files[s3_key]['content']
        return b'file_not_found'
    
    def generate_presigned_url(self, s3_key: str, expiry_hours: int = 1) -> str:
        """Mock presigned URL generation."""
        self.call_history.append({
            'method': 'generate_presigned_url',
            's3_key': s3_key,
            'expiry_hours': expiry_hours
        })
        
        return f"https://mock-s3.amazonaws.com/{s3_key}?expires=1234567890"


class MockPDFService:
    """Mock PDF service for testing."""
    
    def __init__(self):
        self.generated_pdfs = {}
        self.call_history = []
    
    def generate_pdf_from_minuta(
        self, 
        minuta_id: str, 
        upload_to_s3: bool = True
    ) -> tuple[bytes, str, str]:
        """Mock PDF generation from minuta."""
        self.call_history.append({
            'method': 'generate_pdf_from_minuta',
            'minuta_id': minuta_id,
            'upload_to_s3': upload_to_s3
        })
        
        pdf_content = b"Mock PDF content for minuta " + minuta_id.encode()
        filename = f"minuta_{minuta_id}.pdf"
        s3_key = f"documents/{minuta_id}/{filename}"
        
        self.generated_pdfs[minuta_id] = {
            'content': pdf_content,
            'filename': filename,
            's3_key': s3_key
        }
        
        return pdf_content, filename, s3_key
    
    def generate_pdf_from_template(
        self, 
        template_id: str, 
        variaveis: Dict[str, Any]
    ) -> tuple[bytes, str]:
        """Mock PDF generation from template."""
        self.call_history.append({
            'method': 'generate_pdf_from_template',
            'template_id': template_id,
            'variaveis': variaveis
        })
        
        pdf_content = b"Mock PDF content for template " + template_id.encode()
        filename = f"template_{template_id}.pdf"
        
        return pdf_content, filename


class MockTemplateService:
    """Mock template service for testing."""
    
    def __init__(self):
        self.templates = {}
        self.call_history = []
    
    def render_template(
        self, 
        template_id: str, 
        variaveis: Dict[str, Any]
    ) -> str:
        """Mock template rendering."""
        self.call_history.append({
            'method': 'render_template',
            'template_id': template_id,
            'variaveis': variaveis
        })
        
        # Simple mock template rendering
        template_content = f"<h1>Template {template_id}</h1>"
        for key, value in variaveis.items():
            template_content += f"<p>{key}: {value}</p>"
        
        return template_content


class MockSignatureService:
    """Mock signature service for testing."""
    
    def __init__(self):
        self.fluxos = {}
        self.call_history = []
    
    def criar_fluxo_assinatura(
        self, 
        minuta_id: str, 
        signatarios: List[Dict[str, Any]]
    ) -> str:
        """Mock signature flux creation."""
        self.call_history.append({
            'method': 'criar_fluxo_assinatura',
            'minuta_id': minuta_id,
            'signatarios': signatarios
        })
        
        fluxo_id = f"fluxo_{minuta_id}"
        self.fluxos[fluxo_id] = {
            'minuta_id': minuta_id,
            'signatarios': signatarios,
            'status': 'pendente'
        }
        
        return fluxo_id
    
    def cancelar_fluxo(self, fluxo_id: str, motivo: str):
        """Mock flux cancellation."""
        self.call_history.append({
            'method': 'cancelar_fluxo',
            'fluxo_id': fluxo_id,
            'motivo': motivo
        })
        
        if fluxo_id in self.fluxos:
            self.fluxos[fluxo_id]['status'] = 'cancelado'
            self.fluxos[fluxo_id]['motivo_cancelamento'] = motivo
    
    def get_fluxo_status_summary(self, fluxo_id: str) -> Dict[str, Any]:
        """Mock flux status summary."""
        self.call_history.append({
            'method': 'get_fluxo_status_summary',
            'fluxo_id': fluxo_id
        })
        
        if fluxo_id in self.fluxos:
            fluxo = self.fluxos[fluxo_id]
            return {
                'fluxo_id': fluxo_id,
                'status': fluxo['status'],
                'total_signatarios': len(fluxo['signatarios']),
                'assinados': 0,
                'pendentes': len(fluxo['signatarios'])
            }
        
        return {'error': 'Fluxo não encontrado'}


# Global mock instances
mock_ai_service = MockAIServiceManager()
mock_pii_service = MockPIIService()
mock_lexnode_service = MockLexNodeService()
mock_storage_service = MockStorageService()
mock_pdf_service = MockPDFService()
mock_template_service = MockTemplateService()
# mock_signature_service = MockSignatureService()  # REMOVED - service deleted


def setup_mock_services():
    """Setup all mock services for testing."""
    # Patch the AI service manager
    with patch('apps.ai.clients.get_ai_service_manager', return_value=mock_ai_service):
        yield mock_ai_service


def reset_mock_services():
    """Reset all mock services."""
    mock_ai_service.clear_call_history()
    mock_pii_service.call_history = []
    mock_lexnode_service.call_history = []
    mock_storage_service.call_history = []
    mock_pdf_service.call_history = []
    mock_template_service.call_history = []
    # mock_signature_service.call_history = []  # REMOVED - service deleted
    
    # Clear stored data
    mock_pii_service.tokens = {}
    mock_storage_service.files = {}
    mock_pdf_service.generated_pdfs = {}
    mock_template_service.templates = {}
    # mock_signature_service.fluxos = {}  # REMOVED - service deleted
