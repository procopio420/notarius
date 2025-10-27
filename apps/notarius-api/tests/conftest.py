import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def tenant():
    from apps.tenancy.models import Tenant

    return Tenant.objects.create(nome="acme", uf="SP", settings={})


@pytest.fixture
def other_tenant():
    from apps.tenancy.models import Tenant

    return Tenant.objects.create(nome="globex", uf="RJ", settings={})


@pytest.fixture
def user():
    # usuário padrão autenticado
    return User.objects.create_user(username="user", email="user@example.com", password="pass")


@pytest.fixture
def superuser():
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="admin"
    )


@pytest.fixture
def authed_client(api_client, user, tenant):
    api_client.force_authenticate(user=user)
    # Header do middleware multi-tenant
    api_client.credentials(HTTP_X_TENANT_ID=str(tenant.id))
    return api_client


@pytest.fixture
def super_client(api_client, superuser, tenant):
    api_client.force_authenticate(user=superuser)
    api_client.credentials(HTTP_X_TENANT_ID=str(tenant.id))
    return api_client


@pytest.fixture
def authed_client_no_tenant():
    user = User.objects.create_user(username="user2", email="user2@example.com", password="pass")
    client = APIClient()
    client.force_authenticate(user=user)
    # intencionalmente NÃO setamos X-Tenant-ID
    return client


# Factories rápidas (model_bakery cobre 90% dos casos)
@pytest.fixture
def parte(tenant):
    from apps.partes.models import Parte

    return baker.make(
        Parte, tenant=tenant, tipo="pf", nome="João da Silva", nome_normalizado="joao da silva"
    )


@pytest.fixture
def processo(tenant, user):
    from apps.processos.models import Processo

    return baker.make(
        Processo, tenant=tenant, tipo_ato="procuracao", status="rascunho", responsavel=user
    )


@pytest.fixture
def documento(tenant, processo):
    from apps.documentos.models import Documento

    return baker.make(
        Documento,
        tenant=tenant,
        processo=processo,
        tipo="rg",
        s3_key="docs/rg1.pdf",
        hash_sha256=b"\x00" * 32,
        status="novo",
    )
