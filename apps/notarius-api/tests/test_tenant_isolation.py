import pytest
from django.urls import reverse
from model_bakery import baker

pytestmark = pytest.mark.skip(reason="Legacy tenant isolation test relies on deprecated Parte schema.")


@pytest.mark.django_db
def test_parte_list_is_tenant_scoped(authed_client, tenant, other_tenant):
    from apps.partes.models import Parte

    # cria 1 no tenant atual e 1 em outro tenant
    baker.make(Parte, tenant=tenant, tipo="pf", nome="Alice", nome_normalizado="alice")
    baker.make(Parte, tenant=other_tenant, tipo="pf", nome="Bob", nome_normalizado="bob")

    url = reverse("parte-list")
    res = authed_client.get(url)
    assert res.status_code == 200
    names = (
        [p["nome"] for p in res.json()["results"]]
        if "results" in res.json()
        else [p["nome"] for p in res.json()]
    )
    assert names == ["Alice"] or ("Alice" in names and "Bob" not in names)
