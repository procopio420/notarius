import uuid

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_integracao_crud(authed_client):
    url = reverse("integracao-list")
    r = authed_client.post(
        url, {"provedor": "whatsapp", "config_cripto": {"token": "***"}}, format="json"
    )
    assert r.status_code == 201
    iid = r.json()["id"]

    r = authed_client.get(url)
    assert r.status_code == 200

    r = authed_client.patch(
        reverse("integracao-detail", args=[iid]), {"enabled": False}, format="json"
    )
    assert r.status_code == 200
    assert r.json()["enabled"] is False


@pytest.mark.django_db
def test_webhook_and_event(authed_client):
    # webhook
    r = authed_client.post(
        reverse("webhook-list"),
        {"endpoint": "https://example.com/hook", "secret_hmac": "s"},
        format="json",
    )
    assert r.status_code == 201

    # event
    payload = {"evento": "documento.pronto", "payload": {"id": "123"}}
    r = authed_client.post(reverse("webhook-event-list"), payload, format="json")
    assert r.status_code == 201


@pytest.mark.django_db
def test_ai_chunk_crud(authed_client):
    url = reverse("ai-chunk-list")
    payload = {
        "source_type": "template",
        "source_id": str(uuid.uuid4()),
        "chunk_idx": 0,
        "text": "conteúdo",
    }
    r = authed_client.post(url, payload, format="json")
    assert r.status_code == 201
    cid = r.json()["id"]

    r = authed_client.get(url)
    assert r.status_code == 200

    r = authed_client.patch(
        reverse("ai-chunk-detail", args=[cid]), {"text": "novo conteúdo"}, format="json"
    )
    assert r.status_code == 200
