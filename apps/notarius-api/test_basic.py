"""
Basic tests to verify the system is working.
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from apps.tenancy.models import Tenant
from apps.documentos.models import Documento, Minuta, DocumentTemplate
from apps.partes.models import Parte
from apps.processos.models import Processo


class BasicSystemTest(TestCase):
    """Test basic system functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            nome="Test Cartório",
            uf="SP"
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.processo = Processo.objects.create(
            tenant=self.tenant,
            tipo_ato="procuracao",
            status="ativo"
        )
    
    def test_tenant_creation(self):
        """Test tenant creation."""
        self.assertEqual(self.tenant.nome, "Test Cartório")
        self.assertEqual(self.tenant.uf, "SP")
    
    def test_processo_creation(self):
        """Test processo creation."""
        self.assertEqual(self.processo.tenant, self.tenant)
        self.assertEqual(self.processo.tipo_ato, "procuracao")
        self.assertEqual(self.processo.status, "ativo")
    
    def test_minuta_creation(self):
        """Test minuta creation."""
        minuta = Minuta.objects.create(
            tenant=self.tenant,
            processo=self.processo,
            corpo_md="# Test Minuta\n\nThis is a test minuta.",
            variaveis_json={},
            created_by=self.user
        )
        self.assertEqual(minuta.tenant, self.tenant)
        self.assertEqual(minuta.processo, self.processo)
        self.assertEqual(minuta.status, "rascunho")
        self.assertEqual(minuta.gerada_por, "usuario")
    
    def test_documento_creation(self):
        """Test documento creation."""
        documento = Documento.objects.create(
            tenant=self.tenant,
            processo=self.processo,
            s3_key="test/document.pdf",
            hash_sha256=b"test_hash",
            mime="application/pdf",
            pages=1
        )
        self.assertEqual(documento.tenant, self.tenant)
        self.assertEqual(documento.processo, self.processo)
        self.assertEqual(documento.status, "novo")
    
    def test_document_template_creation(self):
        """Test document template creation."""
        template = DocumentTemplate.objects.create(
            tenant=self.tenant,
            name="Test Template",
            document_type="procuracao",
            template_path="procuracao.html",
            is_default=True,
            created_by=self.user
        )
        self.assertEqual(template.tenant, self.tenant)
        self.assertEqual(template.name, "Test Template")
        self.assertEqual(template.document_type, "procuracao")
        self.assertTrue(template.is_default)
    
    def test_parte_creation(self):
        """Test parte creation."""
        parte = Parte.objects.create(
            tenant=self.tenant,
            tipo="pf",
            tipo_pessoa="pf",
            nome_token="token://test/name",
            nome_hash=b"test_hash",
            created_by=self.user
        )
        self.assertEqual(parte.tenant, self.tenant)
        self.assertEqual(parte.tipo, "pf")
        self.assertEqual(parte.tipo_pessoa, "pf")
        self.assertEqual(parte.nome_token, "token://test/name")


class APITest(TestCase):
    """Test API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.tenant = Tenant.objects.create(
            nome="Test Cartório",
            uf="SP"
        )
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        self.processo = Processo.objects.create(
            tenant=self.tenant,
            tipo_ato="procuracao",
            status="ativo"
        )
    
    def test_api_root(self):
        """Test API root endpoint."""
        from django.test import Client
        client = Client()
        response = client.get('/api/')
        # Should return 403 because no authentication (Django returns 403 for authenticated endpoints)
        self.assertEqual(response.status_code, 403)
    
    def test_admin_access(self):
        """Test admin interface access."""
        from django.test import Client
        client = Client()
        response = client.get('/admin/')
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
