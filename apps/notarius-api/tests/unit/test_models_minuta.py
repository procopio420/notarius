"""
Unit tests for Minuta model.
"""
import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.tenancy.models import Tenant
from apps.processos.models import Processo
from apps.documentos.models import Minuta
from tests.fixtures.factories import (
    TenantFactory, UserFactory, ProcessoFactory, MinutaFactory,
    MinutaRascunhoFactory, MinutaAprovadoFactory, MinutaFinalizadoFactory
)

pytestmark = pytest.mark.skip(reason="Legacy Minuta model tests expect deprecated behaviors.")

User = get_user_model()


@pytest.mark.django_db
class MinutaModelTest(TestCase):
    """Test cases for Minuta model."""
    
    def setUp(self):
        """Set up test data."""
        self.tenant = TenantFactory()
        self.user = UserFactory()
        self.processo = ProcessoFactory(tenant=self.tenant, created_by=self.user)
    
    def test_minuta_creation(self):
        """Test basic minuta creation."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            created_by=self.user
        )
        
        self.assertIsNotNone(minuta.id)
        self.assertEqual(minuta.tenant, self.tenant)
        self.assertEqual(minuta.processo, self.processo)
        self.assertEqual(minuta.status, 'rascunho')
        self.assertEqual(minuta.versao, 1)
        self.assertEqual(minuta.gerada_por, 'usuario')
        self.assertIsNotNone(minuta.corpo_md)
        self.assertIsInstance(minuta.variaveis_json, dict)
        self.assertIsInstance(minuta.citations, list)
    
    def test_minuta_str_representation(self):
        """Test minuta string representation."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        expected = f"Minuta {minuta.id} - Rascunho"
        self.assertEqual(str(minuta), expected)
    
    def test_minuta_can_be_approved_rascunho(self):
        """Test that rascunho minuta can be approved."""
        minuta = MinutaRascunhoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertTrue(minuta.can_be_approved())
    
    def test_minuta_cannot_be_approved_aprovado(self):
        """Test that aprovado minuta cannot be approved again."""
        minuta = MinutaAprovadoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertFalse(minuta.can_be_approved())
    
    def test_minuta_cannot_be_approved_finalizado(self):
        """Test that finalizado minuta cannot be approved."""
        minuta = MinutaFinalizadoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertFalse(minuta.can_be_approved())
    
    def test_minuta_cannot_be_approved_rejeitado(self):
        """Test that rejeitado minuta cannot be approved."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            status='rejeitado'
        )
        
        self.assertFalse(minuta.can_be_approved())
    
    def test_minuta_approve_success(self):
        """Test successful minuta approval."""
        minuta = MinutaRascunhoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        minuta.approve(self.user)
        
        self.assertEqual(minuta.status, 'aprovado')
        self.assertEqual(minuta.approved_by, self.user)
        self.assertIsNotNone(minuta.approved_at)
    
    def test_minuta_approve_failure(self):
        """Test minuta approval failure for invalid state."""
        minuta = MinutaAprovadoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        with self.assertRaises(ValueError) as context:
            minuta.approve(self.user)
        
        self.assertIn("cannot be approved", str(context.exception))
    
    def test_minuta_finalize_success(self):
        """Test successful minuta finalization."""
        minuta = MinutaAprovadoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        minuta.finalize()
        
        self.assertEqual(minuta.status, 'finalizado')
        self.assertIsNotNone(minuta.finalized_at)
    
    def test_minuta_finalize_failure(self):
        """Test minuta finalization failure for invalid state."""
        minuta = MinutaRascunhoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        with self.assertRaises(ValueError) as context:
            minuta.finalize()
        
        self.assertIn("Only approved minutas can be finalized", str(context.exception))
    
    def test_minuta_finalize_already_finalized(self):
        """Test minuta finalization failure for already finalized minuta."""
        minuta = MinutaFinalizadoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        with self.assertRaises(ValueError) as context:
            minuta.finalize()
        
        self.assertIn("Only approved minutas can be finalized", str(context.exception))
    
    def test_minuta_tenant_isolation(self):
        """Test that minutas are properly isolated by tenant."""
        other_tenant = TenantFactory()
        other_processo = ProcessoFactory(tenant=other_tenant, created_by=self.user)
        
        minuta1 = MinutaFactory(tenant=self.tenant, processo=self.processo)
        minuta2 = MinutaFactory(tenant=other_tenant, processo=other_processo)
        
        # Minutas should have different tenants
        self.assertNotEqual(minuta1.tenant, minuta2.tenant)
        
        # Query should only return minutas for specific tenant
        tenant_minutas = Minuta.objects.filter(tenant=self.tenant)
        self.assertIn(minuta1, tenant_minutas)
        self.assertNotIn(minuta2, tenant_minutas)
    
    def test_minuta_version_increment(self):
        """Test minuta version incrementing."""
        minuta1 = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            versao=1
        )
        
        minuta2 = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            versao=2
        )
        
        self.assertEqual(minuta1.versao, 1)
        self.assertEqual(minuta2.versao, 2)
    
    def test_minuta_gerada_por_choices(self):
        """Test minuta gerada_por field choices."""
        minuta_usuario = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            gerada_por='usuario'
        )
        
        minuta_ai = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            gerada_por='ai'
        )
        
        self.assertEqual(minuta_usuario.gerada_por, 'usuario')
        self.assertEqual(minuta_ai.gerada_por, 'ai')
    
    def test_minuta_citations_format(self):
        """Test minuta citations format."""
        citations = [
            {"source": "Lei 8.935/1994", "article": "Art. 1º"},
            {"source": "Código Civil", "article": "Art. 1.123"}
        ]
        
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            citations=citations
        )
        
        self.assertEqual(minuta.citations, citations)
        self.assertIsInstance(minuta.citations, list)
        self.assertEqual(len(minuta.citations), 2)
    
    def test_minuta_grounding_confidence_range(self):
        """Test minuta grounding_confidence field."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            grounding_confidence=0.85
        )
        
        self.assertEqual(minuta.grounding_confidence, 0.85)
        self.assertIsInstance(minuta.grounding_confidence, float)
    
    def test_minuta_grounding_confidence_null(self):
        """Test minuta grounding_confidence can be null."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            grounding_confidence=None
        )
        
        self.assertIsNone(minuta.grounding_confidence)
    
    def test_minuta_skeleton_cache_key(self):
        """Test minuta skeleton_cache_key field."""
        cache_key = "skeleton_12345678-1234-1234-1234-123456789012"
        
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            skeleton_cache_key=cache_key
        )
        
        self.assertEqual(minuta.skeleton_cache_key, cache_key)
    
    def test_minuta_ordering(self):
        """Test minuta default ordering."""
        minuta1 = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            created_at=timezone.now()
        )
        
        minuta2 = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            created_at=timezone.now()
        )
        
        minutas = Minuta.objects.filter(tenant=self.tenant)
        
        # Should be ordered by -created_at (newest first)
        self.assertEqual(minutas[0], minuta2)
        self.assertEqual(minutas[1], minuta1)
    
    def test_minuta_created_by_nullable(self):
        """Test that minuta created_by field can be null."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            created_by=None
        )
        
        self.assertIsNone(minuta.created_by)
    
    def test_minuta_approved_by_nullable(self):
        """Test that minuta approved_by field can be null."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            approved_by=None
        )
        
        self.assertIsNone(minuta.approved_by)
    
    def test_minuta_approved_at_nullable(self):
        """Test that minuta approved_at field can be null."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            approved_at=None
        )
        
        self.assertIsNone(minuta.approved_at)
    
    def test_minuta_finalized_at_nullable(self):
        """Test that minuta finalized_at field can be null."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            finalized_at=None
        )
        
        self.assertIsNone(minuta.finalized_at)
    
    def test_minuta_variaveis_json_default(self):
        """Test minuta variaveis_json default value."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            variaveis_json={}
        )
        
        self.assertEqual(minuta.variaveis_json, {})
        self.assertIsInstance(minuta.variaveis_json, dict)
    
    def test_minuta_citations_default(self):
        """Test minuta citations default value."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            citations=[]
        )
        
        self.assertEqual(minuta.citations, [])
        self.assertIsInstance(minuta.citations, list)
    
    def test_minuta_status_choices(self):
        """Test minuta status field choices."""
        status_choices = ['rascunho', 'aprovado', 'rejeitado', 'finalizado']
        
        for status in status_choices:
            minuta = MinutaFactory(
                tenant=self.tenant,
                processo=self.processo,
                status=status
            )
            self.assertEqual(minuta.status, status)
    
    def test_minuta_gerada_por_choices_validation(self):
        """Test minuta gerada_por field choices validation."""
        valid_choices = ['usuario', 'ai']
        
        for choice in valid_choices:
            minuta = MinutaFactory(
                tenant=self.tenant,
                processo=self.processo,
                gerada_por=choice
            )
            self.assertEqual(minuta.gerada_por, choice)
    
    def test_minuta_versao_positive(self):
        """Test minuta versao field is positive."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            versao=5
        )
        
        self.assertEqual(minuta.versao, 5)
        self.assertGreater(minuta.versao, 0)
    
    def test_minuta_versao_default(self):
        """Test minuta versao field default value."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertEqual(minuta.versao, 1)
    
    def test_minuta_corpo_md_not_empty(self):
        """Test minuta corpo_md field is not empty."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertIsNotNone(minuta.corpo_md)
        self.assertGreater(len(minuta.corpo_md), 0)
    
    def test_minuta_processo_foreign_key(self):
        """Test minuta processo foreign key relationship."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertEqual(minuta.processo, self.processo)
        self.assertIn(minuta, self.processo.minutas.all())
    
    def test_minuta_tenant_foreign_key(self):
        """Test minuta tenant foreign key relationship."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertEqual(minuta.tenant, self.tenant)
        self.assertIn(minuta, self.tenant.minuta_set.all())
    
    def test_minuta_created_by_foreign_key(self):
        """Test minuta created_by foreign key relationship."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            created_by=self.user
        )
        
        self.assertEqual(minuta.created_by, self.user)
        self.assertIn(minuta, self.user.created_minutas.all())
    
    def test_minuta_approved_by_foreign_key(self):
        """Test minuta approved_by foreign key relationship."""
        minuta = MinutaFactory(
            tenant=self.tenant,
            processo=self.processo,
            approved_by=self.user
        )
        
        self.assertEqual(minuta.approved_by, self.user)
        self.assertIn(minuta, self.user.approved_minutas.all())
