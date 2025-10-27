import pytest

from apps.tenancy.models import Tenant


@pytest.mark.django_db
def test_tenant_str(tenant):
    assert str(tenant) == f"{tenant.nome}-{tenant.uf}"


@pytest.mark.django_db
def test_tenant_str_custom():
    t = Tenant.objects.create(nome="CartorioCentral", uf="RJ", settings={})
    assert str(t) == "CartorioCentral-RJ"
