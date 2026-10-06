import pytest

from apps.partes.models import Parte

pytestmark = pytest.mark.skip(reason="Legacy tenant manager tests rely on deprecated Parte schema.")


@pytest.mark.django_db
def test_queryset_for_tenant_none_returns_empty(tenant, other_tenant):
    """
    Cobre: TenantQuerySet.for_tenant(None) -> self.none()
    """
    # Cria registros em dois tenants só pra garantir que há dados no banco
    Parte.objects.create(tenant=tenant, tipo="pf", nome="Alice", nome_normalizado="alice")
    Parte.objects.create(tenant=other_tenant, tipo="pf", nome="Bob", nome_normalizado="bob")

    # .all() retorna nosso TenantQuerySet custom → chamamos .for_tenant(None)
    qs = Parte.objects.for_tenant(None)
    assert qs.count() == 0

    # chaining continua vazio
    assert qs.filter(tipo="pf").count() == 0


@pytest.mark.django_db
def test_manager_for_tenant_filters_correctly(tenant, other_tenant):
    """
    Cobre: TenantManager.for_tenant -> self.get_queryset().for_tenant(tenant)
    """
    a = Parte.objects.create(tenant=tenant, tipo="pf", nome="Alice", nome_normalizado="alice")
    b = Parte.objects.create(tenant=other_tenant, tipo="pf", nome="Bob", nome_normalizado="bob")

    # Chamando pelo MANAGER (.objects.for_tenant) garante execução da linha-alvo no manager
    qs = Parte.objects.for_tenant(tenant)
    ids = list(qs.values_list("id", flat=True))

    assert a.id in ids
    assert b.id not in ids
    # sanity: só registros do tenant
    assert qs.count() == 1


@pytest.mark.django_db
def test_manager_for_tenant_none_returns_empty(tenant):
    """
    Extra: manager com tenant=None também deve ser vazio
    """
    Parte.objects.create(tenant=tenant, tipo="pf", nome="Alice", nome_normalizado="alice")
    qs = Parte.objects.for_tenant(None)
    assert qs.count() == 0
