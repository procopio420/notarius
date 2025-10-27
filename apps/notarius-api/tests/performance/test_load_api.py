"""
Performance tests for API endpoints.
"""
import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from apps.tenancy.models import Tenant
from apps.processos.models import Processo
from apps.documentos.models import Minuta
from tests.fixtures.factories import (
    TenantFactory, UserFactory, ProcessoFactory, MinutaFactory
)

User = get_user_model()


@pytest.mark.django_db
class LoadAPITest(TestCase):
    """Test cases for API load testing."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.tenant = TenantFactory()
        self.user = UserFactory()
        self.processo = ProcessoFactory(tenant=self.tenant, created_by=self.user)
        
        # Set tenant in request
        self.client.force_authenticate(user=self.user)
        self.client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
    
    def test_minuta_list_performance(self):
        """Test minuta list endpoint performance."""
        # Create test data
        for i in range(100):
            MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        url = reverse('minuta-list')
        
        # Measure response time
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 1.0)  # Should respond within 1 second
        self.assertEqual(len(response.data['results']), 100)
    
    def test_minuta_create_performance(self):
        """Test minuta creation performance."""
        url = reverse('minuta-list')
        data = {
            'processo': str(self.processo.id),
            'corpo_md': '# Test Minuta\n\nThis is a test minuta.',
            'variaveis_json': {'nome': 'token_123'},
            'status': 'rascunho',
            'gerada_por': 'usuario'
        }
        
        # Measure response time
        start_time = time.time()
        response = self.client.post(url, data, format='json')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertLess(response_time, 0.5)  # Should respond within 500ms
    
    def test_minuta_retrieve_performance(self):
        """Test minuta retrieval performance."""
        minuta = MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        url = reverse('minuta-detail', kwargs={'pk': minuta.id})
        
        # Measure response time
        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 0.2)  # Should respond within 200ms
    
    def test_minuta_update_performance(self):
        """Test minuta update performance."""
        minuta = MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        url = reverse('minuta-detail', kwargs={'pk': minuta.id})
        data = {
            'corpo_md': '# Updated Minuta\n\nThis is an updated minuta.',
            'status': 'aprovado'
        }
        
        # Measure response time
        start_time = time.time()
        response = self.client.patch(url, data, format='json')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 0.3)  # Should respond within 300ms
    
    def test_minuta_delete_performance(self):
        """Test minuta deletion performance."""
        minuta = MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        url = reverse('minuta-detail', kwargs={'pk': minuta.id})
        
        # Measure response time
        start_time = time.time()
        response = self.client.delete(url)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertLess(response_time, 0.2)  # Should respond within 200ms
    
    def test_minuta_search_performance(self):
        """Test minuta search performance."""
        # Create test data with searchable content
        for i in range(50):
            MinutaFactory(
                tenant=self.tenant, 
                processo=self.processo,
                corpo_md=f'# Test Minuta {i}\n\nThis is test minuta number {i}.'
            )
        
        url = reverse('minuta-list')
        
        # Measure response time
        start_time = time.time()
        response = self.client.get(url, {'search': 'test'})
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 0.5)  # Should respond within 500ms
        self.assertEqual(len(response.data['results']), 50)
    
    def test_minuta_filter_performance(self):
        """Test minuta filtering performance."""
        # Create test data with different statuses
        for i in range(25):
            MinutaFactory(tenant=self.tenant, processo=self.processo, status='rascunho')
        for i in range(25):
            MinutaFactory(tenant=self.tenant, processo=self.processo, status='aprovado')
        
        url = reverse('minuta-list')
        
        # Measure response time
        start_time = time.time()
        response = self.client.get(url, {'status': 'rascunho'})
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 0.3)  # Should respond within 300ms
        self.assertEqual(len(response.data['results']), 25)
    
    def test_minuta_ordering_performance(self):
        """Test minuta ordering performance."""
        # Create test data
        for i in range(100):
            MinutaFactory(tenant=self.tenant, processo=self.processo, versao=i)
        
        url = reverse('minuta-list')
        
        # Measure response time
        start_time = time.time()
        response = self.client.get(url, {'ordering': 'versao'})
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 0.5)  # Should respond within 500ms
        self.assertEqual(len(response.data['results']), 100)
    
    def test_minuta_pagination_performance(self):
        """Test minuta pagination performance."""
        # Create test data
        for i in range(1000):
            MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        url = reverse('minuta-list')
        
        # Measure response time
        start_time = time.time()
        response = self.client.get(url, {'page_size': 100})
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 1.0)  # Should respond within 1 second
        self.assertEqual(len(response.data['results']), 100)
    
    def test_concurrent_minuta_creation(self):
        """Test concurrent minuta creation."""
        url = reverse('minuta-list')
        
        def create_minuta():
            data = {
                'processo': str(self.processo.id),
                'corpo_md': '# Test Minuta\n\nThis is a test minuta.',
                'variaveis_json': {'nome': 'token_123'},
                'status': 'rascunho',
                'gerada_por': 'usuario'
            }
            
            client = APIClient()
            client.force_authenticate(user=self.user)
            client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
            
            response = client.post(url, data, format='json')
            return response.status_code
        
        # Create 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_minuta) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status_code == status.HTTP_201_CREATED for status_code in results))
        
        # Check that all minutas were created
        self.assertEqual(Minuta.objects.filter(tenant=self.tenant).count(), 10)
    
    def test_concurrent_minuta_retrieval(self):
        """Test concurrent minuta retrieval."""
        # Create test data
        minutas = [MinutaFactory(tenant=self.tenant, processo=self.processo) for _ in range(10)]
        
        def retrieve_minuta(minuta_id):
            url = reverse('minuta-detail', kwargs={'pk': minuta_id})
            
            client = APIClient()
            client.force_authenticate(user=self.user)
            client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
            
            response = client.get(url)
            return response.status_code
        
        # Create 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(retrieve_minuta, minuta.id) for minuta in minutas]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status_code == status.HTTP_200_OK for status_code in results))
    
    def test_concurrent_minuta_updates(self):
        """Test concurrent minuta updates."""
        # Create test data
        minuta = MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        def update_minuta():
            url = reverse('minuta-detail', kwargs={'pk': minuta.id})
            data = {
                'corpo_md': f'# Updated Minuta\n\nThis is an updated minuta at {time.time()}.',
                'status': 'aprovado'
            }
            
            client = APIClient()
            client.force_authenticate(user=self.user)
            client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
            
            response = client.patch(url, data, format='json')
            return response.status_code
        
        # Create 5 concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_minuta) for _ in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        self.assertEqual(len(results), 5)
        self.assertTrue(all(status_code == status.HTTP_200_OK for status_code in results))
    
    def test_concurrent_minuta_list(self):
        """Test concurrent minuta list requests."""
        # Create test data
        for i in range(100):
            MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        def list_minutas():
            url = reverse('minuta-list')
            
            client = APIClient()
            client.force_authenticate(user=self.user)
            client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
            
            response = client.get(url)
            return response.status_code, len(response.data['results'])
        
        # Create 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(list_minutas) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status_code == status.HTTP_200_OK for status_code, _ in results))
        self.assertTrue(all(count == 100 for _, count in results))
    
    def test_concurrent_minuta_search(self):
        """Test concurrent minuta search requests."""
        # Create test data
        for i in range(50):
            MinutaFactory(
                tenant=self.tenant, 
                processo=self.processo,
                corpo_md=f'# Test Minuta {i}\n\nThis is test minuta number {i}.'
            )
        
        def search_minutas():
            url = reverse('minuta-list')
            
            client = APIClient()
            client.force_authenticate(user=self.user)
            client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
            
            response = client.get(url, {'search': 'test'})
            return response.status_code, len(response.data['results'])
        
        # Create 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(search_minutas) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status_code == status.HTTP_200_OK for status_code, _ in results))
        self.assertTrue(all(count == 50 for _, count in results))
    
    def test_concurrent_minuta_filter(self):
        """Test concurrent minuta filter requests."""
        # Create test data
        for i in range(25):
            MinutaFactory(tenant=self.tenant, processo=self.processo, status='rascunho')
        for i in range(25):
            MinutaFactory(tenant=self.tenant, processo=self.processo, status='aprovado')
        
        def filter_minutas():
            url = reverse('minuta-list')
            
            client = APIClient()
            client.force_authenticate(user=self.user)
            client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
            
            response = client.get(url, {'status': 'rascunho'})
            return response.status_code, len(response.data['results'])
        
        # Create 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(filter_minutas) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status_code == status.HTTP_200_OK for status_code, _ in results))
        self.assertTrue(all(count == 25 for _, count in results))
    
    def test_concurrent_minuta_ordering(self):
        """Test concurrent minuta ordering requests."""
        # Create test data
        for i in range(100):
            MinutaFactory(tenant=self.tenant, processo=self.processo, versao=i)
        
        def order_minutas():
            url = reverse('minuta-list')
            
            client = APIClient()
            client.force_authenticate(user=self.user)
            client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
            
            response = client.get(url, {'ordering': 'versao'})
            return response.status_code, len(response.data['results'])
        
        # Create 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(order_minutas) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status_code == status.HTTP_200_OK for status_code, _ in results))
        self.assertTrue(all(count == 100 for _, count in results))
    
    def test_concurrent_minuta_pagination(self):
        """Test concurrent minuta pagination requests."""
        # Create test data
        for i in range(1000):
            MinutaFactory(tenant=self.tenant, processo=self.processo)
        
        def paginate_minutas():
            url = reverse('minuta-list')
            
            client = APIClient()
            client.force_authenticate(user=self.user)
            client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
            
            response = client.get(url, {'page_size': 100})
            return response.status_code, len(response.data['results'])
        
        # Create 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(paginate_minutas) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status_code == status.HTTP_200_OK for status_code, _ in results))
        self.assertTrue(all(count == 100 for _, count in results))
    
    def test_mixed_concurrent_operations(self):
        """Test mixed concurrent operations."""
        # Create test data
        minutas = [MinutaFactory(tenant=self.tenant, processo=self.processo) for _ in range(10)]
        
        def mixed_operation(operation_type, minuta_id=None):
            client = APIClient()
            client.force_authenticate(user=self.user)
            client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)
            
            if operation_type == 'list':
                url = reverse('minuta-list')
                response = client.get(url)
                return response.status_code, len(response.data['results'])
            elif operation_type == 'retrieve' and minuta_id:
                url = reverse('minuta-detail', kwargs={'pk': minuta_id})
                response = client.get(url)
                return response.status_code, 1
            elif operation_type == 'create':
                url = reverse('minuta-list')
                data = {
                    'processo': str(self.processo.id),
                    'corpo_md': '# Test Minuta\n\nThis is a test minuta.',
                    'variaveis_json': {'nome': 'token_123'},
                    'status': 'rascunho',
                    'gerada_por': 'usuario'
                }
                response = client.post(url, data, format='json')
                return response.status_code, 1
            elif operation_type == 'update' and minuta_id:
                url = reverse('minuta-detail', kwargs={'pk': minuta_id})
                data = {
                    'corpo_md': f'# Updated Minuta\n\nThis is an updated minuta at {time.time()}.',
                    'status': 'aprovado'
                }
                response = client.patch(url, data, format='json')
                return response.status_code, 1
            else:
                return status.HTTP_400_BAD_REQUEST, 0
        
        # Create mixed concurrent requests
        operations = []
        for i in range(5):
            operations.append(('list', None))
            operations.append(('retrieve', minutas[i % len(minutas)].id))
            operations.append(('create', None))
            operations.append(('update', minutas[i % len(minutas)].id))
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(mixed_operation, op_type, minuta_id) for op_type, minuta_id in operations]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        self.assertEqual(len(results), 20)
        self.assertTrue(all(status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED] for status_code, _ in results))
    
    def test_large_payload_performance(self):
        """Test performance with large payloads."""
        url = reverse('minuta-list')
        
        # Create large payload
        large_content = '# Test Minuta\n\n' + 'This is a test minuta. ' * 10000
        large_variables = {f'field_{i}': f'value_{i}' for i in range(1000)}
        
        data = {
            'processo': str(self.processo.id),
            'corpo_md': large_content,
            'variaveis_json': large_variables,
            'status': 'rascunho',
            'gerada_por': 'usuario'
        }
        
        # Measure response time
        start_time = time.time()
        response = self.client.post(url, data, format='json')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertLess(response_time, 2.0)  # Should respond within 2 seconds
    
    def test_large_response_performance(self):
        """Test performance with large responses."""
        # Create large amount of test data
        for i in range(1000):
            MinutaFactory(
                tenant=self.tenant, 
                processo=self.processo,
                corpo_md=f'# Test Minuta {i}\n\nThis is test minuta number {i}.'
            )
        
        url = reverse('minuta-list')
        
        # Measure response time
        start_time = time.time()
        response = self.client.get(url, {'page_size': 1000})
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 2.0)  # Should respond within 2 seconds
        self.assertEqual(len(response.data['results']), 1000)
