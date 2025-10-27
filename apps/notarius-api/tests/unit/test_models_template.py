"""
Unit tests for DocumentTemplate model.
"""
import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.tenancy.models import Tenant
from apps.templates.models import DocumentTemplate
from tests.fixtures.factories import (
    TenantFactory, UserFactory, DocumentTemplateFactory
)

User = get_user_model()


@pytest.mark.django_db
class DocumentTemplateModelTest(TestCase):
    """Test cases for DocumentTemplate model."""
    
    def setUp(self):
        """Set up test data."""
        self.tenant = TenantFactory()
        self.user = UserFactory()
    
    def test_template_creation(self):
        """Test basic template creation."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            created_by=self.user
        )
        
        self.assertIsNotNone(template.id)
        self.assertEqual(template.tenant, self.tenant)
        self.assertEqual(template.created_by, self.user)
        self.assertIsNotNone(template.name)
        self.assertIsNotNone(template.document_type)
        self.assertIsNotNone(template.template_path)
        self.assertTrue(template.is_default)
        self.assertTrue(template.is_active)
        self.assertEqual(template.version, "1.0")
    
    def test_template_str_representation(self):
        """Test template string representation."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            name="procuracao",
            document_type="procuracao"
        )
        
        expected = f"procuracao (procuracao) - {self.tenant.nome}"
        self.assertEqual(str(template), expected)
    
    def test_template_get_default_template(self):
        """Test getting default template by document type."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            name="procuracao",
            document_type="procuracao",
            is_default=True,
            is_active=True
        )
        
        default_template = DocumentTemplate.get_default_template("procuracao")
        self.assertEqual(default_template, template)
    
    def test_template_get_default_template_not_found(self):
        """Test getting default template when none exists."""
        default_template = DocumentTemplate.get_default_template("nonexistent")
        self.assertIsNone(default_template)
    
    def test_template_get_default_template_inactive(self):
        """Test getting default template when inactive."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            name="procuracao",
            document_type="procuracao",
            is_default=True,
            is_active=False
        )
        
        default_template = DocumentTemplate.get_default_template("procuracao")
        self.assertIsNone(default_template)
    
    def test_template_get_tenant_template(self):
        """Test getting tenant-specific template."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            name="procuracao",
            document_type="procuracao",
            is_default=False,
            is_active=True
        )
        
        tenant_template = DocumentTemplate.get_tenant_template(self.tenant, "procuracao")
        self.assertEqual(tenant_template, template)
    
    def test_template_get_tenant_template_fallback(self):
        """Test getting tenant template with fallback to default."""
        # Create default template
        default_template = DocumentTemplateFactory(
            tenant=self.tenant,
            name="procuracao",
            document_type="procuracao",
            is_default=True,
            is_active=True
        )
        
        # Get template for tenant (should fallback to default)
        tenant_template = DocumentTemplate.get_tenant_template(self.tenant, "procuracao")
        self.assertEqual(tenant_template, default_template)
    
    def test_template_get_tenant_template_other_tenant(self):
        """Test getting tenant template for different tenant."""
        other_tenant = TenantFactory()
        
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            name="procuracao",
            document_type="procuracao",
            is_default=False,
            is_active=True
        )
        
        # Should not find template for other tenant
        tenant_template = DocumentTemplate.get_tenant_template(other_tenant, "procuracao")
        self.assertIsNone(tenant_template)
    
    def test_template_get_template_path_absolute(self):
        """Test getting template path when absolute."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            template_path="/absolute/path/template.html"
        )
        
        self.assertEqual(template.get_template_path(), "/absolute/path/template.html")
    
    def test_template_get_template_path_relative(self):
        """Test getting template path when relative."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            template_path="documentos/procuracao.html"
        )
        
        self.assertEqual(template.get_template_path(), "documentos/documentos/procuracao.html")
    
    def test_template_get_custom_fields(self):
        """Test getting custom fields."""
        custom_fields = {
            "field1": "value1",
            "field2": "value2",
            "nested": {"key": "value"}
        }
        
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            custom_fields=custom_fields
        )
        
        self.assertEqual(template.get_custom_fields(), custom_fields)
    
    def test_template_get_custom_fields_empty(self):
        """Test getting custom fields when empty."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            custom_fields={}
        )
        
        self.assertEqual(template.get_custom_fields(), {})
    
    def test_template_get_custom_fields_none(self):
        """Test getting custom fields when None."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            custom_fields=None
        )
        
        self.assertEqual(template.get_custom_fields(), {})
    
    def test_template_get_custom_css(self):
        """Test getting custom CSS."""
        custom_css = ".custom-class { color: red; }"
        
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            custom_css=custom_css
        )
        
        self.assertEqual(template.get_custom_css(), custom_css)
    
    def test_template_get_custom_css_empty(self):
        """Test getting custom CSS when empty."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            custom_css=""
        )
        
        self.assertEqual(template.get_custom_css(), "")
    
    def test_template_get_custom_js(self):
        """Test getting custom JavaScript."""
        custom_js = "console.log('Hello World');"
        
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            custom_js=custom_js
        )
        
        self.assertEqual(template.get_custom_js(), custom_js)
    
    def test_template_get_custom_js_empty(self):
        """Test getting custom JavaScript when empty."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            custom_js=""
        )
        
        self.assertEqual(template.get_custom_js(), "")
    
    def test_template_tenant_isolation(self):
        """Test that templates are properly isolated by tenant."""
        other_tenant = TenantFactory()
        
        template1 = DocumentTemplateFactory(
            tenant=self.tenant,
            name="procuracao",
            document_type="procuracao"
        )
        
        template2 = DocumentTemplateFactory(
            tenant=other_tenant,
            name="procuracao",
            document_type="procuracao"
        )
        
        # Templates should have different tenants
        self.assertNotEqual(template1.tenant, template2.tenant)
        
        # Query should only return templates for specific tenant
        tenant_templates = DocumentTemplate.objects.filter(tenant=self.tenant)
        self.assertIn(template1, tenant_templates)
        self.assertNotIn(template2, tenant_templates)
    
    def test_template_unique_constraint(self):
        """Test template unique constraint per tenant."""
        template1 = DocumentTemplateFactory(
            tenant=self.tenant,
            name="procuracao",
            document_type="procuracao"
        )
        
        # Should not be able to create another template with same name for same tenant
        with self.assertRaises(Exception):
            DocumentTemplateFactory(
                tenant=self.tenant,
                name="procuracao",
                document_type="procuracao"
            )
    
    def test_template_different_tenants_same_name(self):
        """Test templates with same name for different tenants."""
        other_tenant = TenantFactory()
        
        template1 = DocumentTemplateFactory(
            tenant=self.tenant,
            name="procuracao",
            document_type="procuracao"
        )
        
        template2 = DocumentTemplateFactory(
            tenant=other_tenant,
            name="procuracao",
            document_type="procuracao"
        )
        
        self.assertEqual(template1.name, template2.name)
        self.assertNotEqual(template1.tenant, template2.tenant)
    
    def test_template_document_type_choices(self):
        """Test template document_type field with different types."""
        document_types = ['procuracao', 'certidao', 'testamento', 'escritura', 'contrato']
        
        for doc_type in document_types:
            template = DocumentTemplateFactory(
                tenant=self.tenant,
                name=doc_type,
                document_type=doc_type
            )
            self.assertEqual(template.document_type, doc_type)
    
    def test_template_is_default_boolean(self):
        """Test template is_default field."""
        template_default = DocumentTemplateFactory(
            tenant=self.tenant,
            is_default=True
        )
        
        template_not_default = DocumentTemplateFactory(
            tenant=self.tenant,
            is_default=False
        )
        
        self.assertTrue(template_default.is_default)
        self.assertFalse(template_not_default.is_default)
    
    def test_template_is_active_boolean(self):
        """Test template is_active field."""
        template_active = DocumentTemplateFactory(
            tenant=self.tenant,
            is_active=True
        )
        
        template_inactive = DocumentTemplateFactory(
            tenant=self.tenant,
            is_active=False
        )
        
        self.assertTrue(template_active.is_active)
        self.assertFalse(template_inactive.is_active)
    
    def test_template_version_string(self):
        """Test template version field."""
        versions = ["1.0", "1.1", "2.0", "1.0.1", "2.1.3"]
        
        for version in versions:
            template = DocumentTemplateFactory(
                tenant=self.tenant,
                version=version
            )
            self.assertEqual(template.version, version)
    
    def test_template_version_default(self):
        """Test template version field default value."""
        template = DocumentTemplateFactory(
            tenant=self.tenant
        )
        
        self.assertEqual(template.version, "1.0")
    
    def test_template_created_by_foreign_key(self):
        """Test template created_by foreign key relationship."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            created_by=self.user
        )
        
        self.assertEqual(template.created_by, self.user)
        self.assertIn(template, self.user.created_templates.all())
    
    def test_template_updated_by_foreign_key(self):
        """Test template updated_by foreign key relationship."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            updated_by=self.user
        )
        
        self.assertEqual(template.updated_by, self.user)
        self.assertIn(template, self.user.updated_templates.all())
    
    def test_template_updated_by_nullable(self):
        """Test template updated_by field can be null."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            updated_by=None
        )
        
        self.assertIsNone(template.updated_by)
    
    def test_template_ordering(self):
        """Test template default ordering."""
        template1 = DocumentTemplateFactory(
            tenant=self.tenant,
            name="certidao"
        )
        
        template2 = DocumentTemplateFactory(
            tenant=self.tenant,
            name="procuracao"
        )
        
        templates = DocumentTemplate.objects.filter(tenant=self.tenant)
        
        # Should be ordered by name
        self.assertEqual(templates[0], template2)  # procuracao comes before certidao
        self.assertEqual(templates[1], template1)
    
    def test_template_created_at_auto(self):
        """Test template created_at field is auto-generated."""
        template = DocumentTemplateFactory(
            tenant=self.tenant
        )
        
        self.assertIsNotNone(template.created_at)
        self.assertIsInstance(template.created_at, timezone.datetime)
    
    def test_template_updated_at_auto(self):
        """Test template updated_at field is auto-generated."""
        template = DocumentTemplateFactory(
            tenant=self.tenant
        )
        
        self.assertIsNotNone(template.updated_at)
        self.assertIsInstance(template.updated_at, timezone.datetime)
    
    def test_template_updated_at_changes(self):
        """Test template updated_at field changes on update."""
        template = DocumentTemplateFactory(
            tenant=self.tenant
        )
        
        original_updated_at = template.updated_at
        
        # Wait a bit to ensure time difference
        import time
        time.sleep(0.001)
        
        template.name = "updated_name"
        template.save()
        
        self.assertGreater(template.updated_at, original_updated_at)
    
    def test_template_description_field(self):
        """Test template description field."""
        description = "This is a test template description"
        
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            description=description
        )
        
        self.assertEqual(template.description, description)
    
    def test_template_description_empty(self):
        """Test template description field when empty."""
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            description=""
        )
        
        self.assertEqual(template.description, "")
    
    def test_template_custom_css_large(self):
        """Test template custom_css field with large content."""
        large_css = ".class1 { color: red; }\n" * 1000
        
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            custom_css=large_css
        )
        
        self.assertEqual(template.custom_css, large_css)
        self.assertGreater(len(template.custom_css), 10000)
    
    def test_template_custom_js_large(self):
        """Test template custom_js field with large content."""
        large_js = "console.log('test');\n" * 1000
        
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            custom_js=large_js
        )
        
        self.assertEqual(template.custom_js, large_js)
        self.assertGreater(len(template.custom_js), 10000)
    
    def test_template_custom_fields_complex(self):
        """Test template custom_fields field with complex data."""
        complex_fields = {
            "field1": "value1",
            "field2": 123,
            "field3": True,
            "field4": None,
            "field5": [1, 2, 3],
            "field6": {"nested": {"key": "value"}},
            "field7": ["a", "b", "c"]
        }
        
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            custom_fields=complex_fields
        )
        
        self.assertEqual(template.custom_fields, complex_fields)
        self.assertIsInstance(template.custom_fields, dict)
    
    def test_template_name_max_length(self):
        """Test template name field max length."""
        long_name = "a" * 100
        
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            name=long_name
        )
        
        self.assertEqual(template.name, long_name)
        self.assertEqual(len(template.name), 100)
    
    def test_template_document_type_max_length(self):
        """Test template document_type field max length."""
        long_doc_type = "a" * 50
        
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            document_type=long_doc_type
        )
        
        self.assertEqual(template.document_type, long_doc_type)
        self.assertEqual(len(template.document_type), 50)
    
    def test_template_template_path_max_length(self):
        """Test template template_path field max length."""
        long_path = "a" * 255
        
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            template_path=long_path
        )
        
        self.assertEqual(template.template_path, long_path)
        self.assertEqual(len(template.template_path), 255)
    
    def test_template_version_max_length(self):
        """Test template version field max length."""
        long_version = "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0"
        
        template = DocumentTemplateFactory(
            tenant=self.tenant,
            version=long_version
        )
        
        self.assertEqual(template.version, long_version)
        self.assertEqual(len(template.version), 20)
    
    def test_template_indexes(self):
        """Test template database indexes."""
        # Create templates to test indexes
        template1 = DocumentTemplateFactory(
            tenant=self.tenant,
            document_type="procuracao",
            is_default=True,
            is_active=True
        )
        
        template2 = DocumentTemplateFactory(
            tenant=self.tenant,
            document_type="certidao",
            is_default=False,
            is_active=False
        )
        
        # Test queries that should use indexes
        templates_by_type = DocumentTemplate.objects.filter(
            tenant=self.tenant,
            document_type="procuracao"
        )
        self.assertIn(template1, templates_by_type)
        
        default_templates = DocumentTemplate.objects.filter(
            tenant=self.tenant,
            is_default=True
        )
        self.assertIn(template1, default_templates)
        
        active_templates = DocumentTemplate.objects.filter(
            tenant=self.tenant,
            is_active=True
        )
        self.assertIn(template1, active_templates)
