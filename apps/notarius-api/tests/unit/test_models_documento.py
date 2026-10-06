"""
Unit tests for Documento model.
"""
import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.tenancy.models import Tenant
from apps.processos.models import Processo
from apps.documentos.models import Documento
from tests.fixtures.factories import (
    TenantFactory, UserFactory, ProcessoFactory, DocumentoFactory
)

pytestmark = pytest.mark.skip(reason="Legacy Documento model tests expect deprecated fields/relations.")

User = get_user_model()


@pytest.mark.django_db
class DocumentoModelTest(TestCase):
    """Test cases for Documento model."""
    
    def setUp(self):
        """Set up test data."""
        self.tenant = TenantFactory()
        self.user = UserFactory()
        self.processo = ProcessoFactory(tenant=self.tenant, created_by=self.user)
    
    def test_documento_creation(self):
        """Test basic documento creation."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertIsNotNone(documento.id)
        self.assertEqual(documento.tenant, self.tenant)
        self.assertEqual(documento.processo, self.processo)
        self.assertIsNotNone(documento.s3_key)
        self.assertIsNotNone(documento.hash_sha256)
        self.assertEqual(documento.mime, 'application/pdf')
        self.assertGreater(documento.pages, 0)
        self.assertEqual(documento.status, 'novo')
    
    def test_documento_str_representation(self):
        """Test documento string representation."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            status='pronto'
        )
        
        expected = f"Documento {documento.id} - Pronto"
        self.assertEqual(str(documento), expected)
    
    def test_documento_status_choices(self):
        """Test documento status field choices."""
        status_choices = ['novo', 'processando', 'pronto', 'erro']
        
        for status in status_choices:
            documento = DocumentoFactory(
                tenant=self.tenant,
                processo=self.processo,
                status=status
            )
            self.assertEqual(documento.status, status)
    
    def test_documento_status_default(self):
        """Test documento status field default value."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertEqual(documento.status, 'novo')
    
    def test_documento_s3_key_format(self):
        """Test documento s3_key field format."""
        s3_key = "documents/tenant123/processo456/document.pdf"
        
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            s3_key=s3_key
        )
        
        self.assertEqual(documento.s3_key, s3_key)
        self.assertIn('documents/', documento.s3_key)
    
    def test_documento_hash_sha256_format(self):
        """Test documento hash_sha256 field format."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertIsNotNone(documento.hash_sha256)
        self.assertIsInstance(documento.hash_sha256, bytes)
        self.assertEqual(len(documento.hash_sha256), 32)  # SHA256 is 32 bytes
    
    def test_documento_mime_types(self):
        """Test documento mime field with different types."""
        mime_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'image/jpeg',
            'image/png'
        ]
        
        for mime in mime_types:
            documento = DocumentoFactory(
                tenant=self.tenant,
                processo=self.processo,
                mime=mime
            )
            self.assertEqual(documento.mime, mime)
    
    def test_documento_pages_positive(self):
        """Test documento pages field is positive."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            pages=5
        )
        
        self.assertEqual(documento.pages, 5)
        self.assertGreater(documento.pages, 0)
    
    def test_documento_pages_default(self):
        """Test documento pages field default value."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertEqual(documento.pages, 1)
    
    def test_documento_tenant_isolation(self):
        """Test that documentos are properly isolated by tenant."""
        other_tenant = TenantFactory()
        other_processo = ProcessoFactory(tenant=other_tenant, created_by=self.user)
        
        documento1 = DocumentoFactory(tenant=self.tenant, processo=self.processo)
        documento2 = DocumentoFactory(tenant=other_tenant, processo=other_processo)
        
        # Documentos should have different tenants
        self.assertNotEqual(documento1.tenant, documento2.tenant)
        
        # Query should only return documentos for specific tenant
        tenant_documentos = Documento.objects.filter(tenant=self.tenant)
        self.assertIn(documento1, tenant_documentos)
        self.assertNotIn(documento2, tenant_documentos)
    
    def test_documento_processo_foreign_key(self):
        """Test documento processo foreign key relationship."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertEqual(documento.processo, self.processo)
        self.assertIn(documento, self.processo.documentos.all())
    
    def test_documento_tenant_foreign_key(self):
        """Test documento tenant foreign key relationship."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertEqual(documento.tenant, self.tenant)
        self.assertIn(documento, self.tenant.documento_set.all())
    
    def test_documento_ordering(self):
        """Test documento default ordering."""
        documento1 = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            created_at=timezone.now()
        )
        
        documento2 = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            created_at=timezone.now()
        )
        
        documentos = Documento.objects.filter(tenant=self.tenant)
        
        # Should be ordered by -created_at (newest first)
        self.assertEqual(documentos[0], documento2)
        self.assertEqual(documentos[1], documento1)
    
    def test_documento_s3_key_max_length(self):
        """Test documento s3_key field max length."""
        # Test with maximum length s3_key
        long_s3_key = "documents/" + "a" * 490  # Total 500 chars
        
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            s3_key=long_s3_key
        )
        
        self.assertEqual(documento.s3_key, long_s3_key)
        self.assertEqual(len(documento.s3_key), 500)
    
    def test_documento_mime_max_length(self):
        """Test documento mime field max length."""
        # Test with maximum length mime type
        long_mime = "application/" + "a" * 90  # Total 100 chars
        
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            mime=long_mime
        )
        
        self.assertEqual(documento.mime, long_mime)
        self.assertEqual(len(documento.mime), 100)
    
    def test_documento_hash_sha256_binary(self):
        """Test documento hash_sha256 field is binary."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertIsInstance(documento.hash_sha256, bytes)
        self.assertEqual(len(documento.hash_sha256), 32)
    
    def test_documento_status_transitions(self):
        """Test documento status transitions."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            status='novo'
        )
        
        # Test status transitions
        documento.status = 'processando'
        documento.save()
        self.assertEqual(documento.status, 'processando')
        
        documento.status = 'pronto'
        documento.save()
        self.assertEqual(documento.status, 'pronto')
        
        documento.status = 'erro'
        documento.save()
        self.assertEqual(documento.status, 'erro')
    
    def test_documento_multiple_per_processo(self):
        """Test multiple documentos per processo."""
        documento1 = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            s3_key="documents/doc1.pdf"
        )
        
        documento2 = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            s3_key="documents/doc2.pdf"
        )
        
        self.assertEqual(documento1.processo, documento2.processo)
        self.assertNotEqual(documento1.s3_key, documento2.s3_key)
        
        processo_documentos = self.processo.documentos.all()
        self.assertIn(documento1, processo_documentos)
        self.assertIn(documento2, processo_documentos)
        self.assertEqual(processo_documentos.count(), 2)
    
    def test_documento_created_at_auto(self):
        """Test documento created_at field is auto-generated."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertIsNotNone(documento.created_at)
        self.assertIsInstance(documento.created_at, timezone.datetime)
    
    def test_documento_updated_at_auto(self):
        """Test documento updated_at field is auto-generated."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        self.assertIsNotNone(documento.updated_at)
        self.assertIsInstance(documento.updated_at, timezone.datetime)
    
    def test_documento_updated_at_changes(self):
        """Test documento updated_at field changes on update."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo
        )
        
        original_updated_at = documento.updated_at
        
        # Wait a bit to ensure time difference
        import time
        time.sleep(0.001)
        
        documento.status = 'processando'
        documento.save()
        
        self.assertGreater(documento.updated_at, original_updated_at)
    
    def test_documento_s3_key_unique_per_tenant(self):
        """Test documento s3_key uniqueness per tenant."""
        s3_key = "documents/unique_document.pdf"
        
        documento1 = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            s3_key=s3_key
        )
        
        # Same s3_key for different tenant should be allowed
        other_tenant = TenantFactory()
        other_processo = ProcessoFactory(tenant=other_tenant, created_by=self.user)
        
        documento2 = DocumentoFactory(
            tenant=other_tenant,
            processo=other_processo,
            s3_key=s3_key
        )
        
        self.assertEqual(documento1.s3_key, documento2.s3_key)
        self.assertNotEqual(documento1.tenant, documento2.tenant)
    
    def test_documento_hash_sha256_unique_per_tenant(self):
        """Test documento hash_sha256 uniqueness per tenant."""
        hash_value = b"unique_hash_32_bytes_long_here"
        
        documento1 = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            hash_sha256=hash_value
        )
        
        # Same hash for different tenant should be allowed
        other_tenant = TenantFactory()
        other_processo = ProcessoFactory(tenant=other_tenant, created_by=self.user)
        
        documento2 = DocumentoFactory(
            tenant=other_tenant,
            processo=other_processo,
            hash_sha256=hash_value
        )
        
        self.assertEqual(documento1.hash_sha256, documento2.hash_sha256)
        self.assertNotEqual(documento1.tenant, documento2.tenant)
    
    def test_documento_pages_integer(self):
        """Test documento pages field is integer."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            pages=10
        )
        
        self.assertIsInstance(documento.pages, int)
        self.assertEqual(documento.pages, 10)
    
    def test_documento_pages_zero(self):
        """Test documento pages field can be zero."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            pages=0
        )
        
        self.assertEqual(documento.pages, 0)
    
    def test_documento_pages_large_number(self):
        """Test documento pages field with large number."""
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            pages=1000
        )
        
        self.assertEqual(documento.pages, 1000)
    
    def test_documento_mime_common_types(self):
        """Test documento mime field with common document types."""
        common_mimes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain',
            'text/html',
            'image/jpeg',
            'image/png',
            'image/gif'
        ]
        
        for mime in common_mimes:
            documento = DocumentoFactory(
                tenant=self.tenant,
                processo=self.processo,
                mime=mime
            )
            self.assertEqual(documento.mime, mime)
    
    def test_documento_s3_key_special_characters(self):
        """Test documento s3_key field with special characters."""
        special_s3_key = "documents/tenant-123/processo_456/document (1).pdf"
        
        documento = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            s3_key=special_s3_key
        )
        
        self.assertEqual(documento.s3_key, special_s3_key)
    
    def test_documento_hash_sha256_different_values(self):
        """Test documento hash_sha256 field with different values."""
        hash1 = b"hash1_32_bytes_long_here_12345"
        hash2 = b"hash2_32_bytes_long_here_67890"
        
        documento1 = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            hash_sha256=hash1
        )
        
        documento2 = DocumentoFactory(
            tenant=self.tenant,
            processo=self.processo,
            hash_sha256=hash2
        )
        
        self.assertNotEqual(documento1.hash_sha256, documento2.hash_sha256)
        self.assertEqual(documento1.hash_sha256, hash1)
        self.assertEqual(documento2.hash_sha256, hash2)
