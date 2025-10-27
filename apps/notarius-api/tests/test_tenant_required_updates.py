import pytest
from django.urls import reverse

MSG = "Tenant não definido. Envie X-Tenant-ID."


@pytest.mark.django_db
def test_patch_requires_tenant_header_returns_403(authed_client, authed_client_no_tenant):
    # cria um recurso válido (com header)
    r = authed_client.post(reverse("parte-list"), {"tipo": "pf", "nome": "Fulano"}, format="json")
    assert r.status_code == 201
    pid = r.json()["id"]

    # tenta PATCH sem header de tenant
    r = authed_client_no_tenant.patch(
        reverse("parte-detail", args=[pid]), {"nome": "Fulano Edit"}, format="json"
    )
    assert r.status_code == 403
    assert r.json().get("detail") == MSG


@pytest.mark.django_db
def test_delete_requires_tenant_header_returns_403(authed_client, authed_client_no_tenant):
    r = authed_client.post(reverse("parte-list"), {"tipo": "pf", "nome": "Sicrana"}, format="json")
    assert r.status_code == 201
    pid = r.json()["id"]

    r = authed_client_no_tenant.delete(reverse("parte-detail", args=[pid]))
    assert r.status_code == 403
    assert r.json().get("detail") == MSG


@pytest.mark.django_db
def test_patch_with_tenant_ok(authed_client):
    r = authed_client.post(reverse("parte-list"), {"tipo": "pf", "nome": "Maria"}, format="json")
    assert r.status_code == 201
    pid = r.json()["id"]

    r = authed_client.patch(
        reverse("parte-detail", args=[pid]), {"nome": "Maria S."}, format="json"
    )
    assert r.status_code == 200
    assert r.json()["nome"] == "Maria S."


@pytest.mark.django_db
def test_delete_with_tenant_ok(authed_client):
    r = authed_client.post(reverse("parte-list"), {"tipo": "pf", "nome": "Carlos"}, format="json")
    assert r.status_code == 201
    pid = r.json()["id"]

    r = authed_client.delete(reverse("parte-detail", args=[pid]))
    assert r.status_code in (204, 200)
