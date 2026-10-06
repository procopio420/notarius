"""
Security tests for injection attacks.
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.tenancy.models import Tenant
from apps.processos.models import Processo
from apps.documentos.models import Minuta
from tests.fixtures.factories import TenantFactory, UserFactory, ProcessoFactory
from tests.fixtures.test_data import SecurityTestPayloads

User = get_user_model()


pytestmark = pytest.mark.skip(reason="Legacy security suite targets deprecated minuta endpoints.")


@pytest.mark.django_db
class SecurityInjectionTest(TestCase):
    """Test cases for injection attack prevention."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.tenant = TenantFactory()
        self.user = UserFactory()
        self.processo = ProcessoFactory(tenant=self.tenant, created_by=self.user)
        
        # Set tenant in request
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
    
    def test_sql_injection_minuta_corpo_md(self):
        """Test SQL injection in minuta corpo_md field."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': payload,
                'variaveis_json': {'nome': 'token_123'},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause SQL injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            # Should either succeed or fail with validation error
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_sql_injection_minuta_variaveis_json(self):
        """Test SQL injection in minuta variaveis_json field."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': '# Test Minuta',
                'variaveis_json': {'nome': payload},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause SQL injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_sql_injection_minuta_search(self):
        """Test SQL injection in minuta search parameter."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            response = self.client.get(url, {'search': payload})
            
            # Should not cause SQL injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_sql_injection_minuta_filter(self):
        """Test SQL injection in minuta filter parameters."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            response = self.client.get(url, {'status': payload})
            
            # Should not cause SQL injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_xss_minuta_corpo_md(self):
        """Test XSS in minuta corpo_md field."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.XSS_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': payload,
                'variaveis_json': {'nome': 'token_123'},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause XSS
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
            
            if response.status_code == status.HTTP_201_CREATED:
                # Check that the payload is stored as-is (not executed)
                minuta_id = response.data['id']
                minuta = Minuta.objects.get(id=minuta_id)
                self.assertEqual(minuta.corpo_md, payload)
    
    def test_xss_minuta_variaveis_json(self):
        """Test XSS in minuta variaveis_json field."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.XSS_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': '# Test Minuta',
                'variaveis_json': {'nome': payload},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause XSS
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
            
            if response.status_code == status.HTTP_201_CREATED:
                # Check that the payload is stored as-is (not executed)
                minuta_id = response.data['id']
                minuta = Minuta.objects.get(id=minuta_id)
                self.assertEqual(minuta.variaveis_json['nome'], payload)
    
    def test_xss_minuta_search(self):
        """Test XSS in minuta search parameter."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.XSS_PAYLOADS:
            response = self.client.get(url, {'search': payload})
            
            # Should not cause XSS
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_command_injection_minuta_corpo_md(self):
        """Test command injection in minuta corpo_md field."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.COMMAND_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': payload,
                'variaveis_json': {'nome': 'token_123'},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause command injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_command_injection_minuta_variaveis_json(self):
        """Test command injection in minuta variaveis_json field."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.COMMAND_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': '# Test Minuta',
                'variaveis_json': {'nome': payload},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause command injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_ldap_injection_minuta_corpo_md(self):
        """Test LDAP injection in minuta corpo_md field."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.LDAP_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': payload,
                'variaveis_json': {'nome': 'token_123'},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause LDAP injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_ldap_injection_minuta_variaveis_json(self):
        """Test LDAP injection in minuta variaveis_json field."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.LDAP_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': '# Test Minuta',
                'variaveis_json': {'nome': payload},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause LDAP injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_xml_injection_minuta_corpo_md(self):
        """Test XML injection in minuta corpo_md field."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.XML_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': payload,
                'variaveis_json': {'nome': 'token_123'},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause XML injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_xml_injection_minuta_variaveis_json(self):
        """Test XML injection in minuta variaveis_json field."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.XML_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': '# Test Minuta',
                'variaveis_json': {'nome': payload},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause XML injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_injection_in_url_parameters(self):
        """Test injection in URL parameters."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            response = self.client.get(url, {'search': payload, 'status': payload})
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_injection_in_headers(self):
        """Test injection in HTTP headers."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            response = self.client.get(url, HTTP_X_TENANT_ID=payload)
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            # Should fail with validation error for invalid tenant ID
            self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])
    
    def test_injection_in_content_type(self):
        """Test injection in Content-Type header."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            response = self.client.post(
                url, 
                data={'test': 'data'}, 
                content_type=f'application/json; {payload}'
            )
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def test_injection_in_user_agent(self):
        """Test injection in User-Agent header."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            response = self.client.get(url, HTTP_USER_AGENT=payload)
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_injection_in_referer(self):
        """Test injection in Referer header."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            response = self.client.get(url, HTTP_REFERER=payload)
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_injection_in_accept_header(self):
        """Test injection in Accept header."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            response = self.client.get(url, HTTP_ACCEPT=payload)
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_injection_in_authorization_header(self):
        """Test injection in Authorization header."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            response = self.client.get(url, HTTP_AUTHORIZATION=payload)
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            # Should fail with authentication error
            self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_injection_in_custom_headers(self):
        """Test injection in custom headers."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            response = self.client.get(url, HTTP_X_CUSTOM_HEADER=payload)
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_injection_in_json_payload(self):
        """Test injection in JSON payload structure."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': '# Test Minuta',
                'variaveis_json': {payload: 'value'},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_injection_in_nested_json(self):
        """Test injection in nested JSON structure."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': '# Test Minuta',
                'variaveis_json': {
                    'nested': {
                        'key': payload,
                        'another_key': 'value'
                    }
                },
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_injection_in_array_json(self):
        """Test injection in JSON array."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': '# Test Minuta',
                'variaveis_json': {'array': [payload, 'value1', 'value2']},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_injection_in_citations(self):
        """Test injection in citations field."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': '# Test Minuta',
                'variaveis_json': {'nome': 'token_123'},
                'citations': [{'source': payload, 'article': 'Art. 1º'}],
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
    
    def test_injection_in_skeleton_cache_key(self):
        """Test injection in skeleton_cache_key field."""
        url = reverse('minuta-list')
        
        for payload in SecurityTestPayloads.SQL_INJECTION_PAYLOADS:
            data = {
                'processo': str(self.processo.id),
                'corpo_md': '# Test Minuta',
                'variaveis_json': {'nome': 'token_123'},
                'skeleton_cache_key': payload,
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            response = self.client.post(url, data, format='json')
            
            # Should not cause injection
            self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_400_BAD_REQUEST])
