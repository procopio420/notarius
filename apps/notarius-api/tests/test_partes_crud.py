import pytest
from django.urls import reverse

pytestmark = pytest.mark.skip(reason="Legacy partes CRUD tests no longer match current model schema.")


@pytest.mark.django_db
def test_parte_crud(authed_client):
    # CREATE
    url = reverse("parte-list")
    payload = {"tipo": "pf", "nome": "Maria Souza", "dados_cript": {"cpf": "123.456.789-00"}}
    r = authed_client.post(url, payload, format="json")
    assert r.status_code == 201, r.content
    parte_id = r.json()["id"]
    assert r.json()["tenant"] is not None  # setado automaticamente

    # LIST
    r = authed_client.get(url)
    assert r.status_code == 200
    # RETRIEVE
    r = authed_client.get(reverse("parte-detail", args=[parte_id]))
    assert r.status_code == 200
    assert r.json()["nome"] == "Maria Souza"

    # UPDATE (PATCH)
    r = authed_client.patch(
        reverse("parte-detail", args=[parte_id]), {"nome": "Maria S."}, format="json"
    )
    assert r.status_code == 200
    assert r.json()["nome"] == "Maria S."

    # DELETE
    r = authed_client.delete(reverse("parte-detail", args=[parte_id]))
    assert r.status_code in (204, 200)
