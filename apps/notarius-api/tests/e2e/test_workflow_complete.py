"""
End-to-end tests for complete workflows.
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.tenancy.models import Tenant
from apps.processos.models import Processo
from apps.partes.models import Parte
from apps.documentos.models import Minuta, Documento
from apps.templates.models import DocumentTemplate
from tests.fixtures.factories import (
    TenantFactory, UserFactory, ProcessoFactory, ParteFactory,
    MinutaFactory, DocumentoFactory, DocumentTemplateFactory
)
from tests.fixtures.mock_services import setup_mock_services

User = get_user_model()


pytestmark = pytest.mark.skip(reason="Legacy workflow e2e suite references deprecated APIs.")


@pytest.mark.django_db
class CompleteWorkflowTest(TestCase):
    """Test cases for complete end-to-end workflows."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.tenant = TenantFactory()
        self.user = UserFactory()
        self.processo = ProcessoFactory(tenant=self.tenant, created_by=self.user)
        
        # Set tenant in request
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
    
    def test_complete_minuta_workflow(self):
        """Test complete minuta workflow from creation to finalization."""
        # Step 1: Create minuta
        url = reverse('minuta-list')
        data = {
            'processo': str(self.processo.id),
            'corpo_md': '# Test Minuta\n\nThis is a test minuta for workflow testing.',
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
            'status': 'rascunho',
            'gerada_por': 'usuario'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        minuta_id = response.data['id']
        
        # Step 2: Retrieve minuta
        url = reverse('minuta-detail', kwargs={'pk': minuta_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'rascunho')
        
        # Step 3: Update minuta
        data = {
            'corpo_md': '# Updated Test Minuta\n\nThis is an updated test minuta for workflow testing.',
            'status': 'rascunho'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 4: Approve minuta
        url = reverse('approve-minuta', kwargs={'minuta_id': minuta_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'aprovado')
        
        # Step 5: Finalize minuta
        url = reverse('finalize-minuta', kwargs={'minuta_id': minuta_id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'finalizado')
        
        # Step 6: Verify final state
        url = reverse('minuta-detail', kwargs={'pk': minuta_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'finalizado')
        self.assertIsNotNone(response.data['finalized_at'])
    
    def test_complete_document_workflow(self):
        """Test complete document workflow from template to final document."""
        # Step 1: Create document template
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            name='procuracao',
            document_type='procuracao',
            template_path='documentos/procuracao.html',
            is_default=True,
            is_active=True,
            created_by=self.user
        )
        
        # Step 2: Create minuta
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            corpo_md='# Procuracao\n\nEste é um documento de procuração.',
            variaveis_json={
                'nome_outorgante': 'token_12345678-1234-1234-1234-123456789012',
                'nome_outorgado': 'token_87654321-4321-4321-4321-210987654321'
            },
            status='rascunho',
            created_by=self.user
        )
        
        # Step 3: Approve minuta
        minuta.approve(self.user)
        self.assertEqual(minuta.status, 'aprovado')
        
        # Step 4: Finalize minuta (should create final document)
        url = reverse('finalize-minuta', kwargs={'minuta_id': minuta.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 5: Verify final document was created
        documentos = Documento.objects.filter(tenant=self.tenant, processo=self.processo)
        self.assertEqual(documentos.count(), 1)
        
        documento = documentos.first()
        self.assertEqual(documento.status, 'pronto')
        self.assertEqual(documento.mime, 'application/pdf')
        self.assertGreater(documento.pages, 0)
    
    def test_complete_parte_workflow(self):
        """Test complete parte workflow from creation to association."""
        # Step 1: Create parte
        parte = ParteFactory(
            tenant=self.tenant,
            tipo='pf',
            tipo_pessoa='pf',
            nome_token='token_12345678-1234-1234-1234-123456789012',
            nome_hash=b'hashed_john_doe',
            cpf_token='token_cpf_12345678900',
            cpf_hash=b'hashed_cpf_12345678900',
            endereco_token='token_endereco_rua_das_flores_123',
            email_token='token_email_joao_silva_email_com',
            telefone_token='token_telefone_21999999999',
            created_by=self.user
        )
        
        # Step 2: Verify parte creation
        self.assertEqual(parte.tenant, self.tenant)
        self.assertEqual(parte.tipo, 'pf')
        self.assertEqual(parte.tipo_pessoa, 'pf')
        self.assertIsNotNone(parte.nome_token)
        self.assertIsNotNone(parte.nome_hash)
        
        # Step 3: Update parte
        parte.tipo = 'pj'
        parte.tipo_pessoa = 'pj'
        parte.cnpj_token = 'token_cnpj_12345678000190'
        parte.cnpj_hash = b'hashed_cnpj_12345678000190'
        parte.save()
        
        # Step 4: Verify parte update
        parte.refresh_from_db()
        self.assertEqual(parte.tipo, 'pj')
        self.assertEqual(parte.tipo_pessoa, 'pj')
        self.assertIsNotNone(parte.cnpj_token)
        self.assertIsNotNone(parte.cnpj_hash)
    
    def test_complete_processo_workflow(self):
        """Test complete processo workflow from creation to completion."""
        # Step 1: Create processo
        processo = ProcessoFactory(
            tenant=self.tenant,
            numero='PROC-123456',
            tipo_ato='compra_e_venda',
            status='ativo',
            created_by=self.user
        )
        
        # Step 2: Verify processo creation
        self.assertEqual(processo.tenant, self.tenant)
        self.assertEqual(processo.numero, 'PROC-123456')
        self.assertEqual(processo.tipo_ato, 'compra_e_venda')
        self.assertEqual(processo.status, 'ativo')
        
        # Step 3: Create related partes
        parte1 = ParteFactory(
            tenant=self.tenant,
            tipo='pf',
            tipo_pessoa='pf',
            nome_token='token_vendedor',
            created_by=self.user
        )
        
        parte2 = ParteFactory(
            tenant=self.tenant,
            tipo='pf',
            tipo_pessoa='pf',
            nome_token='token_comprador',
            created_by=self.user
        )
        
        # Step 4: Create related minutas
        minuta1 = MinutaFactory(
            tenant=self.tenant,
            processo=processo,
            corpo_md='# Minuta de Compra e Venda\n\nEste é um documento de compra e venda.',
            status='rascunho',
            created_by=self.user
        )
        
        minuta2 = MinutaFactory(
            tenant=self.tenant,
            processo=processo,
            corpo_md='# Minuta de Contrato\n\nEste é um contrato de compra e venda.',
            status='rascunho',
            created_by=self.user
        )
        
        # Step 5: Approve minutas
        minuta1.approve(self.user)
        minuta2.approve(self.user)
        
        # Step 6: Finalize minutas
        minuta1.finalize()
        minuta2.finalize()
        
        # Step 7: Verify final state
        processo.refresh_from_db()
        self.assertEqual(processo.status, 'ativo')
        
        minutas = processo.minutas.all()
        self.assertEqual(minutas.count(), 2)
        self.assertTrue(all(minuta.status == 'finalizado' for minuta in minutas))
        
        documentos = processo.documentos.all()
        self.assertEqual(documentos.count(), 2)
        self.assertTrue(all(documento.status == 'pronto' for documento in documentos))
    
    def test_complete_template_workflow(self):
        """Test complete template workflow from creation to usage."""
        # Step 1: Create default template
        default_template = DocumentTemplateFactory(
            tenant=self.tenant,
            name='procuracao',
            document_type='procuracao',
            template_path='documentos/procuracao.html',
            is_default=True,
            is_active=True,
            created_by=self.user
        )
        
        # Step 2: Create tenant-specific template
        tenant_template = DocumentTemplateFactory(
            tenant=self.tenant,
            name='procuracao_custom',
            document_type='procuracao',
            template_path='documentos/procuracao_custom.html',
            is_default=False,
            is_active=True,
            custom_css='.custom-class { color: red; }',
            custom_js='console.log("Custom template loaded");',
            custom_fields={'field1': 'value1', 'field2': 'value2'},
            created_by=self.user
        )
        
        # Step 3: Test template retrieval
        retrieved_template = DocumentTemplate.get_tenant_template(self.tenant, 'procuracao')
        self.assertEqual(retrieved_template, tenant_template)
        
        # Step 4: Test template path resolution
        self.assertEqual(tenant_template.get_template_path(), 'documentos/documentos/procuracao_custom.html')
        
        # Step 5: Test custom fields retrieval
        custom_fields = tenant_template.get_custom_fields()
        self.assertEqual(custom_fields['field1'], 'value1')
        self.assertEqual(custom_fields['field2'], 'value2')
        
        # Step 6: Test custom CSS retrieval
        custom_css = tenant_template.get_custom_css()
        self.assertEqual(custom_css, '.custom-class { color: red; }')
        
        # Step 7: Test custom JS retrieval
        custom_js = tenant_template.get_custom_js()
        self.assertEqual(custom_js, 'console.log("Custom template loaded");')
        
        # Step 8: Deactivate template
        tenant_template.is_active = False
        tenant_template.save()
        
        # Step 9: Test fallback to default template
        retrieved_template = DocumentTemplate.get_tenant_template(self.tenant, 'procuracao')
        self.assertEqual(retrieved_template, default_template)
    
    def test_complete_ai_workflow(self):
        """Test complete AI workflow from intent to final document."""
        with setup_mock_services() as mock_ai_service:
            # Step 1: Generate minuta from intent
            url = reverse('generate-minuta')
            data = {
                'intent': 'Criar uma procuração para João Silva representar Maria Santos em uma compra e venda de imóvel',
                'processo_id': str(self.processo.id)
            }
            
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            minuta_id = response.data['id']
            
            # Step 2: Verify minuta was created with AI data
            minuta = Minuta.objects.get(id=minuta_id)
            self.assertEqual(minuta.gerada_por, 'ai')
            self.assertEqual(minuta.status, 'rascunho')
            self.assertIsNotNone(minuta.corpo_md)
            self.assertIsNotNone(minuta.variaveis_json)
            self.assertIsNotNone(minuta.citations)
            self.assertIsNotNone(minuta.grounding_confidence)
            
            # Step 3: Approve AI-generated minuta
            url = reverse('approve-minuta', kwargs={'minuta_id': minuta_id})
            response = self.client.post(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'aprovado')
            
            # Step 4: Finalize AI-generated minuta
            url = reverse('finalize-minuta', kwargs={'minuta_id': minuta_id})
            response = self.client.post(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['status'], 'finalizado')
            
            # Step 5: Verify final document was created
            documentos = Documento.objects.filter(tenant=self.tenant, processo=self.processo)
            self.assertEqual(documentos.count(), 1)
            
            documento = documentos.first()
            self.assertEqual(documento.status, 'pronto')
            self.assertEqual(documento.mime, 'application/pdf')
    
    def test_complete_multi_tenant_workflow(self):
        """Test complete workflow with multiple tenants."""
        # Step 1: Create second tenant
        other_tenant = TenantFactory()
        other_user = UserFactory()
        other_processo = ProcessoFactory(tenant=other_tenant, created_by=other_user)
        
        # Step 2: Create minuta for first tenant
        minuta1 = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            corpo_md='# Minuta Tenant 1\n\nThis is a minuta for tenant 1.',
            status='rascunho',
            created_by=self.user
        )
        
        # Step 3: Create minuta for second tenant
        minuta2 = MinutaFactory(
            tenant=other_tenant,
            processo=other_processo,
            corpo_md='# Minuta Tenant 2\n\nThis is a minuta for tenant 2.',
            status='rascunho',
            created_by=other_user
        )
        
        # Step 4: Verify tenant isolation
        self.assertNotEqual(minuta1.tenant, minuta2.tenant)
        self.assertNotEqual(minuta1.processo, minuta2.processo)
        
        # Step 5: Test cross-tenant access prevention
        url = reverse('minuta-detail', kwargs={'pk': minuta2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Step 6: Test tenant-specific queries
        tenant1_minutas = Minuta.objects.filter(tenant=self.tenant)
        tenant2_minutas = Minuta.objects.filter(tenant=other_tenant)
        
        self.assertIn(minuta1, tenant1_minutas)
        self.assertNotIn(minuta2, tenant1_minutas)
        self.assertIn(minuta2, tenant2_minutas)
        self.assertNotIn(minuta1, tenant2_minutas)
    
    def test_complete_error_recovery_workflow(self):
        """Test complete workflow with error recovery."""
        # Step 1: Create minuta
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            corpo_md='# Test Minuta\n\nThis is a test minuta for error recovery.',
            status='rascunho',
            created_by=self.user
        )
        
        # Step 2: Try to approve minuta that's already approved (should fail)
        minuta.approve(self.user)
        self.assertEqual(minuta.status, 'aprovado')
        
        url = reverse('approve-minuta', kwargs={'minuta_id': minuta.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Step 3: Try to finalize minuta that's not approved (should fail)
        minuta.status = 'rascunho'
        minuta.save()
        
        url = reverse('finalize-minuta', kwargs={'minuta_id': minuta.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Step 4: Recover by approving and finalizing
        minuta.approve(self.user)
        self.assertEqual(minuta.status, 'aprovado')
        
        url = reverse('finalize-minuta', kwargs={'minuta_id': minuta.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'finalizado')
        
        # Step 5: Verify final state
        minuta.refresh_from_db()
        self.assertEqual(minuta.status, 'finalizado')
        self.assertIsNotNone(minuta.finalized_at)
    
    def test_complete_large_data_workflow(self):
        """Test complete workflow with large data."""
        # Step 1: Create minuta with large content
        large_content = '# Test Minuta\n\n' + 'This is a test minuta with large content. ' * 1000
        large_variables = {f'field_{i}': f'value_{i}' for i in range(100)}
        large_citations = [{'source': f'Source {i}', 'article': f'Art. {i}'} for i in range(50)]
        
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            corpo_md=large_content,
            variaveis_json=large_variables,
            citations=large_citations,
            status='rascunho',
            created_by=self.user
        )
        
        # Step 2: Verify large data was stored correctly
        self.assertEqual(len(minuta.corpo_md), len(large_content))
        self.assertEqual(len(minuta.variaveis_json), len(large_variables))
        self.assertEqual(len(minuta.citations), len(large_citations))
        
        # Step 3: Approve minuta with large data
        minuta.approve(self.user)
        self.assertEqual(minuta.status, 'aprovado')
        
        # Step 4: Finalize minuta with large data
        minuta.finalize()
        self.assertEqual(minuta.status, 'finalizado')
        
        # Step 5: Verify final document was created
        documentos = Documento.objects.filter(tenant=self.tenant, processo=self.processo)
        self.assertEqual(documentos.count(), 1)
        
        documento = documentos.first()
        self.assertEqual(documento.status, 'pronto')
        self.assertEqual(documento.mime, 'application/pdf')
        self.assertGreater(documento.pages, 0)
    
    def test_complete_unicode_workflow(self):
        """Test complete workflow with unicode content."""
        # Step 1: Create minuta with unicode content
        unicode_content = '# Test Minuta\n\nUnicode: João Silva Santos, ção, ñ, ü, é, á, í, ó, ú'
        unicode_variables = {
            'nome_outorgante': 'token_João_Silva_Santos',
            'nome_outorgado': 'token_Maria_Santos_Silva',
            'endereco': 'token_Rua_das_Flores_123_Centro_Rio_de_Janeiro_RJ'
        }
        unicode_citations = [
            {'source': 'Lei 8.935/1994', 'article': 'Art. 1º - Dos Cartórios'},
            {'source': 'Código Civil', 'article': 'Art. 1.123 - Da Compra e Venda'}
        ]
        
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            corpo_md=unicode_content,
            variaveis_json=unicode_variables,
            citations=unicode_citations,
            status='rascunho',
            created_by=self.user
        )
        
        # Step 2: Verify unicode data was stored correctly
        self.assertEqual(minuta.corpo_md, unicode_content)
        self.assertEqual(minuta.variaveis_json, unicode_variables)
        self.assertEqual(minuta.citations, unicode_citations)
        
        # Step 3: Approve minuta with unicode data
        minuta.approve(self.user)
        self.assertEqual(minuta.status, 'aprovado')
        
        # Step 4: Finalize minuta with unicode data
        minuta.finalize()
        self.assertEqual(minuta.status, 'finalizado')
        
        # Step 5: Verify final document was created
        documentos = Documento.objects.filter(tenant=self.tenant, processo=self.processo)
        self.assertEqual(documentos.count(), 1)
        
        documento = documentos.first()
        self.assertEqual(documento.status, 'pronto')
        self.assertEqual(documento.mime, 'application/pdf')
        self.assertGreater(documento.pages, 0)
