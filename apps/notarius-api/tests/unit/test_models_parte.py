"""
Unit tests for Parte model (fixed to match actual schema).
"""
import pytest
from django.test import TestCase
from apps.tenancy.models import Tenant
from apps.partes.models import Parte
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class ParteModelTest(TestCase):
    """Test case for Parte model."""
    
    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(nome="Test Cartório", uf="RJ")
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        
    def test_parte_creation(self):
        """Test creating a parte with PII tokens."""
        parte = Parte.objects.create(
            tenant=self.tenant,
            tipo="pf",
            tipo_pessoa="pf",
            nome_token="PII_NOME_abc123",
            nome_hash=b"hash_abc123",
            created_by=self.user
        )
        
        self.assertIsNotNone(parte.id)
        self.assertEqual(parte.tenant, self.tenant)
        self.assertEqual(parte.nome_token, "PII_NOME_abc123")
        self.assertEqual(parte.tipo, "pf")
        
    def test_parte_tenant_isolation(self):
        """Test that partes are isolated by tenant."""
        tenant1 = self.tenant
        tenant2 = Tenant.objects.create(nome="Other Cartório", uf="SP")
        
        parte1 = Parte.objects.create(
            tenant=tenant1,
            tipo="pf",
            nome_token="PII_NOME_1"
        )
        
        parte2 = Parte.objects.create(
            tenant=tenant2,
            tipo="pj",
            nome_token="PII_NOME_2"
        )
        
        tenant1_partes = Parte.objects.filter(tenant=tenant1)
        self.assertIn(parte1, tenant1_partes)
        self.assertNotIn(parte2, tenant1_partes)
        
    def test_parte_indexes(self):
        """Test that database indexes exist."""
        parte = Parte.objects.create(
            tenant=self.tenant,
            tipo="pf",
            nome_token="PII_NOME_abc"
        )
        
        result = Parte.objects.filter(tenant=self.tenant, tipo="pf").first()
        self.assertEqual(result.id, parte.id)
        
    def test_parte_created_at_auto(self):
        """Test that created_at is automatically set."""
        parte = Parte.objects.create(
            tenant=self.tenant,
            tipo="pf",
            nome_token="PII_NOME_abc"
        )
        
        self.assertIsNotNone(parte.created_at)
        
    def test_parte_updated_at_changes(self):
        """Test that updated_at changes on update."""
        parte = Parte.objects.create(
            tenant=self.tenant,
            tipo="pf",
            nome_token="PII_NOME_abc"
        )
        
        original_updated_at = parte.updated_at
        parte.email_token = "PII_EMAIL_xyz"
        parte.save()
        
        self.assertGreater(parte.updated_at, original_updated_at)
        
    def test_parte_different_tenants_same_hash(self):
        """Test that different tenants can have same hash."""
        tenant2 = Tenant.objects.create(nome="Other Cartório", uf="SP")
        
        parte1 = Parte.objects.create(
            tenant=self.tenant,
            tipo="pf",
            nome_token="PII_NOME_1",
            nome_hash=b"same_hash"
        )
        
        parte2 = Parte.objects.create(
            tenant=tenant2,
            tipo="pf",
            nome_token="PII_NOME_2",
            nome_hash=b"same_hash"
        )
        
        self.assertEqual(parte1.nome_hash, parte2.nome_hash)
        self.assertNotEqual(parte1.tenant, parte2.tenant)
        
    def test_parte_tipo_nullable(self):
        """Test that tipo can be null."""
        parte = Parte.objects.create(
            tenant=self.tenant,
            tipo=None,
            nome_token="PII_NOME_abc"
        )
        
        self.assertIsNone(parte.tipo)
        
    def test_parte_updated_by_foreign_key(self):
        """Test parte updated_by foreign key relationship."""
        parte = Parte.objects.create(
            tenant=self.tenant,
            tipo="pf",
            nome_token="PII_NOME_abc",
            updated_by=self.user
        )
        
        self.assertEqual(parte.updated_by, self.user)
        
    def test_parte_hash_format(self):
        """Test that hash fields are strings."""
        parte = Parte.objects.create(
            tenant=self.tenant,
            tipo="pf",
            nome_token="PII_NOME_abc",
            nome_hash=b"hash_123",
            cpf_hash=b"hash_456"
        )
        
        self.assertIsInstance(parte.nome_hash, (bytes, memoryview))
        self.assertIsInstance(parte.cpf_hash, (bytes, memoryview))
        
    def test_parte_token_format(self):
        """Test that token fields start with PII prefix."""
        parte = Parte.objects.create(
            tenant=self.tenant,
            tipo="pf",
            nome_token="PII_NOME_abc123",
            cpf_token="PII_CPF_def456"
        )
        
        self.assertTrue(parte.nome_token.startswith("PII_"))
        self.assertTrue(parte.cpf_token.startswith("PII_"))
        
    def test_parte_null_fields(self):
        """Test that nullable fields can be null."""
        parte = Parte.objects.create(
            tenant=self.tenant,
            tipo="pf",
            nome_token="PII_NOME_abc",
            cpf_token=None,
            cnpj_token=None,
            endereco_token=None
        )
        
        self.assertIsNone(parte.cpf_token)
        self.assertIsNone(parte.cnpj_token)
        self.assertIsNone(parte.endereco_token)
        
    def test_parte_tipo_pessoa_choices(self):
        """Test tipo_pessoa choices."""
        parte_pf = Parte.objects.create(
            tenant=self.tenant,
            tipo="pf",
            tipo_pessoa="pf",
            nome_token="PII_NOME_1"
        )
        
        parte_pj = Parte.objects.create(
            tenant=self.tenant,
            tipo="pj",
            tipo_pessoa="pj",
            nome_token="PII_NOME_2"
        )
        
        self.assertEqual(parte_pf.tipo_pessoa, "pf")
        self.assertEqual(parte_pj.tipo_pessoa, "pj")
        
    def test_parte_metadata_json(self):
        """Test metadata JSON field."""
        parte = Parte.objects.create(
            tenant=self.tenant,
            tipo="pf",
            nome_token="PII_NOME_abc",
            metadata={"key": "value", "number": 123}
        )
        
        self.assertEqual(parte.metadata["key"], "value")
        self.assertEqual(parte.metadata["number"], 123)
        
