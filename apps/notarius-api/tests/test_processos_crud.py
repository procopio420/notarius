import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_processo_and_relations(authed_client, parte):
    # CREATE processo
    r = authed_client.post(reverse("processo-list"), {"tipo_ato": "procuracao"}, format="json")
    assert r.status_code == 201, r.content
    proc_id = r.json()["id"]

    # CREATE processo-parte
    payload = {"processo": proc_id, "parte": parte.id, "papel": "outorgante"}
    r = authed_client.post(reverse("processo-parte-list"), payload, format="json")
    assert r.status_code == 201, r.content

    # LIST processo-partes
    r = authed_client.get(reverse("processo-parte-list"), {"processo": proc_id})
    assert r.status_code == 200
    data = r.json()
    items = []
    if isinstance(data, dict) and "results" in data:
        return data.get("results", data)
    items = data
    assert len(items) == 1
    return None
