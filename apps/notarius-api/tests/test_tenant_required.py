import pytest
from django.urls import reverse

# Endpoints multi-tenant (exclui tenants e audit-logs, que podem ser read-only/fora do tenant)
ENDPOINTS = [
    "parte-list",
    "processo-list",
    "processo-parte-list",
    "documento-list",
    "minuta-list",
    "checklist-list",
    "financeiro-item-list",
    "integracao-list",
    "webhook-list",
    "webhook-event-list",
    "ai-chunk-list",
]

MSG = "Tenant não definido. Envie X-Tenant-ID."


@pytest.mark.django_db
@pytest.mark.parametrize("name", ENDPOINTS)
def test_list_requires_tenant_header_returns_403(authed_client_no_tenant, name):
    url = reverse(name)
    res = authed_client_no_tenant.get(url)
    assert res.status_code == 403
    assert res.json().get("detail") == MSG


@pytest.mark.django_db
def test_post_parte_requires_tenant_header_returns_403(authed_client_no_tenant):
    url = reverse("parte-list")
    payload = {"tipo": "pf", "nome": "Fulano"}
    res = authed_client_no_tenant.post(url, payload, format="json")
    assert res.status_code == 403
    assert res.json().get("detail") == MSG


@pytest.mark.django_db
def test_post_processo_requires_tenant_header_returns_403(authed_client_no_tenant):
    url = reverse("processo-list")
    payload = {"tipo_ato": "procuracao"}
    res = authed_client_no_tenant.post(url, payload, format="json")
    assert res.status_code == 403
    assert res.json().get("detail") == MSG
