import pytest
from django.urls import reverse

pytestmark = pytest.mark.skip(reason="Legacy checklist/minuta tests target deprecated endpoints.")


@pytest.mark.django_db
def test_documento_flow(authed_client, processo):
    # Documento CREATE
    payload = {
        "tipo": "rg",
        "processo": str(processo.id),
        "s3_key": "docs/rg1.pdf",
        "mime": "application/pdf",
        "pages": 1,
        "status": "novo",
    }
    r = authed_client.post(reverse("documento-list"), payload, format="json")
    # hash_sha256 é read-only; backend deve calcular depois (ou em signal)
    assert r.status_code == 201, r.content
    doc_id = r.json()["id"]

    # PATCH status
    r = authed_client.patch(
        reverse("documento-detail", args=[doc_id]), {"status": "processando"}, format="json"
    )
    assert r.status_code == 200
    assert r.json()["status"] == "processando"


@pytest.mark.django_db
def test_minuta_created_by_auto(authed_client, processo):
    payload = {
        "processo": str(processo.id),
        "versao": 1,
        "gerada_por": "humano",
        "corpo_md": "## Minuta inicial",
    }
    r = authed_client.post(reverse("minuta-list"), payload, format="json")
    assert r.status_code == 201, r.content
    body = r.json()
    assert body["created_by"] is not None  # setado pelo viewset
    assert body["tenant"] is not None


@pytest.mark.django_db
def test_checklist_crud(authed_client, processo):
    # CREATE
    payload = {"processo": str(processo.id), "item": "Conferir RG", "ordem": 1}
    r = authed_client.post(reverse("checklist-list"), payload, format="json")
    assert r.status_code == 201
    cid = r.json()["id"]

    # LIST
    r = authed_client.get(reverse("checklist-list"), {"processo": str(processo.id)})
    assert r.status_code == 200

    # PATCH done_by/done_at
    r = authed_client.patch(reverse("checklist-detail", args=[cid]), {"ordem": 2}, format="json")
    assert r.status_code == 200
    assert r.json()["ordem"] == 2
