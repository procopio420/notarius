"""
Integration tests for Minuta API endpoints.
"""
import pytest
import json
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.tenancy.models import Tenant
from apps.processos.models import Processo
from apps.documentos.models import Minuta
from tests.fixtures.factories import (
    TenantFactory, UserFactory, ProcessoFactory, MinutaFactory,
    MinutaRascunhoFactory, MinutaAprovadoFactory
)

User = get_user_model()


@pytest.mark.django_db
class MinutaAPITest(TestCase):
    """Test cases for Minuta API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.tenant = TenantFactory()
        self.user = UserFactory()
        self.processo = ProcessoFactory(tenant=self.tenant, created_by=self.user)
        
        # Set tenant in request
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
    
    def test_minuta_list(self):
        """Test minuta list endpoint."""
        minuta1 = MinutaFactory(tenant=self.tenant, processo=self.processo)
        minuta2 = MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        url = reverse('minuta-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_minuta_create(self):
        """Test minuta creation."""
        url = reverse('minuta-list')
        data = {
            'processo': str(self.processo.id),
            'corpo_md': '# Test Minuta\n\nThis is a test minuta.',
            'variaveis_json': {'nome': 'token_123'},
            'status': 'rascunho',
            'gerada_por': 'usuario'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Minuta.objects.count(), 1)
    
    def test_minuta_retrieve(self):
        """Test minuta retrieval."""
        minuta = MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        url = reverse('minuta-detail', kwargs={'pk': minuta.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], str(minuta.id))
    
    def test_minuta_update(self):
        """Test minuta update."""
        minuta = MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        url = reverse('minuta-detail', kwargs={'pk': minuta.id})
        data = {
            'corpo_md': '# Updated Minuta\n\nThis is an updated minuta.',
            'status': 'aprovado'
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        minuta.refresh_from_db()
        self.assertEqual(minuta.status, 'aprovado')
    
    def test_minuta_delete(self):
        """Test minuta deletion."""
        minuta = MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        url = reverse('minuta-detail', kwargs={'pk': minuta.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Minuta.objects.filter(id=minuta.id).exists())
    
    def test_minuta_tenant_isolation(self):
        """Test minuta tenant isolation."""
        other_tenant = TenantFactory()
        other_processo = ProcessoFactory(tenant=other_tenant, created_by=self.user)
        other_minuta = MinutaFactory(tenant=other_tenant, processo=other_processo)
        
        url = reverse('minuta-detail', kwargs={'pk': other_minuta.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_minuta_filter_by_status(self):
        """Test minuta filtering by status."""
        MinutaFactory(tenant=self.tenant, processo=self.processo, status='rascunho')
        MinutaFactory(tenant=self.tenant, processo=self.processo, status='aprovado')
        
        url = reverse('minuta-list')
        response = self.client.get(url, {'status': 'rascunho'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['status'], 'rascunho')
    
    def test_minuta_filter_by_processo(self):
        """Test minuta filtering by processo."""
        other_processo = ProcessoFactory(tenant=self.tenant, created_by=self.user)
        
        MinutaFactory(tenant=self.tenant, processo=self.processo)
        MinutaFactory(tenant=self.tenant, processo=other_processo)
        
        url = reverse('minuta-list')
        response = self.client.get(url, {'processo': str(self.processo.id)})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_minuta_filter_by_gerada_por(self):
        """Test minuta filtering by gerada_por."""
        MinutaFactory(tenant=self.tenant, processo=self.processo, gerada_por='usuario')
        MinutaFactory(tenant=self.tenant, processo=self.processo, gerada_por='ai')
        
        url = reverse('minuta-list')
        response = self.client.get(url, {'gerada_por': 'usuario'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['gerada_por'], 'usuario')
    
    def test_minuta_search(self):
        """Test minuta search functionality."""
        MinutaFactory(
            tenant=self.tenant, 
            processo=self.processo, 
            corpo_md='# Test Minuta\n\nThis is a test minuta.'
        )
        
        url = reverse('minuta-list')
        response = self.client.get(url, {'search': 'test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_minuta_ordering(self):
        """Test minuta ordering."""
        minuta1 = MinutaFactory(tenant=self.tenant, processo=self.processo, versao=1)
        minuta2 = MinutaFactory(tenant=self.tenant, processo=self.processo, versao=2)
        
        url = reverse('minuta-list')
        response = self.client.get(url, {'ordering': 'versao'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['versao'], 1)
        self.assertEqual(response.data['results'][1]['versao'], 2)
    
    def test_minuta_ordering_desc(self):
        """Test minuta ordering descending."""
        minuta1 = MinutaFactory(tenant=self.tenant, processo=self.processo, versao=1)
        minuta2 = MinutaFactory(tenant=self.tenant, processo=self.processo, versao=2)
        
        url = reverse('minuta-list')
        response = self.client.get(url, {'ordering': '-versao'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['versao'], 2)
        self.assertEqual(response.data['results'][1]['versao'], 1)
    
    def test_minuta_unauthorized_access(self):
        """Test minuta unauthorized access."""
        self.client.force_authenticate(user=None)
        
        url = reverse('minuta-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_minuta_invalid_data(self):
        """Test minuta creation with invalid data."""
        url = reverse('minuta-list')
        data = {
            'processo': 'invalid-uuid',
            'corpo_md': '',
            'status': 'invalid_status'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_minuta_missing_required_fields(self):
        """Test minuta creation with missing required fields."""
        url = reverse('minuta-list')
        data = {
            'corpo_md': '# Test Minuta'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_minuta_large_content(self):
        """Test minuta creation with large content."""
        large_content = '# Test Minuta\n\n' + 'This is a test minuta. ' * 1000
        
        url = reverse('minuta-list')
        data = {
            'processo': str(self.processo.id),
            'corpo_md': large_content,
            'variaveis_json': {'nome': 'token_123'},
            'status': 'rascunho',
            'gerada_por': 'usuario'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Minuta.objects.count(), 1)
    
    def test_minuta_special_characters(self):
        """Test minuta creation with special characters."""
        special_content = '# Test Minuta\n\nSpecial chars: !@#$%^&*()_+-=[]{}|;:,.<>?'
        
        url = reverse('minuta-list')
        data = {
            'processo': str(self.processo.id),
            'corpo_md': special_content,
            'variaveis_json': {'nome': 'token_123'},
            'status': 'rascunho',
            'gerada_por': 'usuario'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Minuta.objects.count(), 1)
    
    def test_minuta_unicode_content(self):
        """Test minuta creation with unicode content."""
        unicode_content = '# Test Minuta\n\nUnicode: João Silva Santos, ção, ñ, ü'
        
        url = reverse('minuta-list')
        data = {
            'processo': str(self.processo.id),
            'corpo_md': unicode_content,
            'variaveis_json': {'nome': 'token_123'},
            'status': 'rascunho',
            'gerada_por': 'usuario'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Minuta.objects.count(), 1)
    
    def test_minuta_json_variables(self):
        """Test minuta creation with JSON variables."""
        json_variables = {
            'nome_outorgante': 'token_123',
            'nome_outorgado': 'token_456',
            'endereco': 'token_789',
            'nested': {'key': 'value'}
        }
        
        url = reverse('minuta-list')
        data = {
            'processo': str(self.processo.id),
            'corpo_md': '# Test Minuta',
            'variaveis_json': json_variables,
            'status': 'rascunho',
            'gerada_por': 'usuario'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Minuta.objects.count(), 1)
    
    def test_minuta_citations(self):
        """Test minuta creation with citations."""
        citations = [
            {'source': 'Lei 8.935/1994', 'article': 'Art. 1º'},
            {'source': 'Código Civil', 'article': 'Art. 1.123'}
        ]
        
        url = reverse('minuta-list')
        data = {
            'processo': str(self.processo.id),
            'corpo_md': '# Test Minuta',
            'variaveis_json': {'nome': 'token_123'},
            'citations': citations,
            'status': 'rascunho',
            'gerada_por': 'usuario'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Minuta.objects.count(), 1)
    
    def test_minuta_grounding_confidence(self):
        """Test minuta creation with grounding confidence."""
        url = reverse('minuta-list')
        data = {
            'processo': str(self.processo.id),
            'corpo_md': '# Test Minuta',
            'variaveis_json': {'nome': 'token_123'},
            'grounding_confidence': 0.85,
            'status': 'rascunho',
            'gerada_por': 'usuario'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Minuta.objects.count(), 1)
    
    def test_minuta_skeleton_cache_key(self):
        """Test minuta creation with skeleton cache key."""
        cache_key = "skeleton_12345678-1234-1234-1234-123456789012"
        
        url = reverse('minuta-list')
        data = {
            'processo': str(self.processo.id),
            'corpo_md': '# Test Minuta',
            'variaveis_json': {'nome': 'token_123'},
            'skeleton_cache_key': cache_key,
            'status': 'rascunho',
            'gerada_por': 'usuario'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Minuta.objects.count(), 1)
    
    def test_minuta_pagination(self):
        """Test minuta pagination."""
        # Create multiple minutas
        for i in range(25):
            MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        url = reverse('minuta-list')
        response = self.client.get(url, {'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['next'])
    
    def test_minuta_pagination_page_2(self):
        """Test minuta pagination page 2."""
        # Create multiple minutas
        for i in range(25):
            MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        url = reverse('minuta-list')
        response = self.client.get(url, {'page': 2, 'page_size': 10})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 10)
        self.assertIsNotNone(response.data['previous'])
    
    def test_minuta_pagination_invalid_page(self):
        """Test minuta pagination with invalid page."""
        url = reverse('minuta-list')
        response = self.client.get(url, {'page': 999})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_minuta_pagination_negative_page(self):
        """Test minuta pagination with negative page."""
        url = reverse('minuta-list')
        response = self.client.get(url, {'page': -1})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_minuta_pagination_zero_page(self):
        """Test minuta pagination with zero page."""
        url = reverse('minuta-list')
        response = self.client.get(url, {'page': 0})
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_minuta_pagination_large_page_size(self):
        """Test minuta pagination with large page size."""
        url = reverse('minuta-list')
        response = self.client.get(url, {'page_size': 1000})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be limited by max_page_size setting
    
    def test_minuta_pagination_negative_page_size(self):
        """Test minuta pagination with negative page size."""
        url = reverse('minuta-list')
        response = self.client.get(url, {'page_size': -1})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should use default page size
    
    def test_minuta_pagination_zero_page_size(self):
        """Test minuta pagination with zero page size."""
        url = reverse('minuta-list')
        response = self.client.get(url, {'page_size': 0})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should use default page size
