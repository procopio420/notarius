"""
Unit tests for Processo model.
Only tests that match actual model schema.
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from apps.tenancy.models import Tenant
from apps.processos.models import Processo
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class ProcessoModelTest(TestCase):
    """Test case for Processo model."""
    
    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(nome="Test Cartório", uf="RJ")
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        
    def test_processo_creation(self):
        """Test creating a processo with valid data."""
        processo = Processo.objects.create(
            tenant=self.tenant,
            tipo_ato="procuracao",
            status="rascunho",
            responsavel=self.user
        )
        
        self.assertIsNotNone(processo.id)
        self.assertEqual(processo.tenant, self.tenant)
        self.assertEqual(processo.responsavel, self.user)
        self.assertEqual(processo.tipo_ato, "procuracao")
        self.assertEqual(processo.status, "rascunho")
        
    def test_processo_tenant_isolation(self):
        """Test that processos are isolated by tenant."""
        tenant1 = self.tenant
        tenant2 = Tenant.objects.create(nome="Other Cartório", uf="SP")
        
        processo1 = Processo.objects.create(
            tenant=tenant1,
            tipo_ato="procuracao",
            status="rascunho"
        )
        
        processo2 = Processo.objects.create(
            tenant=tenant2,
            tipo_ato="certidao",
            status="rascunho"
        )
        
        tenant1_processos = Processo.objects.filter(tenant=tenant1)
        self.assertIn(processo1, tenant1_processos)
        self.assertNotIn(processo2, tenant1_processos)
        
    def test_processo_created_at_auto(self):
        """Test that created_at is automatically set."""
        processo = Processo.objects.create(
            tenant=self.tenant,
            tipo_ato="procuracao",
            status="rascunho"
        )
        
        self.assertIsNotNone(processo.created_at)
        
    def test_processo_updated_at_changes(self):
        """Test that updated_at changes on update."""
        processo = Processo.objects.create(
            tenant=self.tenant,
            tipo_ato="procuracao",
            status="rascunho"
        )
        
        original_updated_at = processo.updated_at
        processo.status = "analise"
        processo.save()
        
        self.assertGreater(processo.updated_at, original_updated_at)
        
    def test_processo_status_choices(self):
        """Test processo status choices."""
        valid_statuses = ["rascunho", "analise", "assinatura", "selagem", "arquivado", "cancelado"]
        
        for status in valid_statuses:
            processo = Processo.objects.create(
                tenant=self.tenant,
                tipo_ato="procuracao",
                status=status
            )
            self.assertEqual(processo.status, status)
            
    def test_processo_tipo_ato_validation(self):
        """Test tipo_ato field."""
        processo = Processo.objects.create(
            tenant=self.tenant,
            tipo_ato="compra_e_venda",
            status="rascunho"
        )
        
        self.assertEqual(processo.tipo_ato, "compra_e_venda")
        
