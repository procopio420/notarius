"""Tests for `GenerateMinutaFromIntentView`."""

from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.urls import reverse

from apps.ai_documents.models import AIGeneratedMinuta
from apps.documentos.models import Minuta
from apps.processos.models import Processo


pytestmark = pytest.mark.django_db


def _make_ai_response():
    return {
        "corpo_md": "# Minuta gerada\n\nCorpo do documento.",
        "variaveis_json": {"nome": "Fulano"},
        "citations": [{"source": "Lei 8.935/1994", "article": "Art. 1º"}],
        "grounding_confidence": 0.87,
        "skeleton_cache_key": "cache-key",
        "parsed_intent": {"tipo": "procuracao"},
    }


def _build_service_mock(ai_response):
    service = MagicMock()
    service.generate_minuta_from_intent = AsyncMock(return_value=ai_response)
    return service


def _endpoint():
    return reverse("generate-minuta-alias")


def test_generate_minuta_success(authed_client, processo):
    endpoint = _endpoint()
    ai_response = _make_ai_response()

    initial_minuta_count = Minuta.objects.count()
    initial_ai_count = AIGeneratedMinuta.objects.count()

    with patch("apps.ai_documents.views.get_ai_service_manager") as mock_manager:
        mock_manager.return_value = _build_service_mock(ai_response)

        payload = {
            "intent": "Gerar uma minuta de procuração pública completa.",
            "processo_id": str(processo.id),
        }
        response = authed_client.post(endpoint, payload, format="json")

    assert response.status_code == 201
    data = response.json()
    assert data["corpo_md"] == ai_response["corpo_md"]
    assert Minuta.objects.count() == initial_minuta_count + 1
    assert AIGeneratedMinuta.objects.count() == initial_ai_count + 1

    new_minuta = Minuta.objects.order_by("-created_at").first()
    assert new_minuta.processo_id == processo.id
    assert new_minuta.variaveis_json == ai_response["variaveis_json"]

    ai_record = AIGeneratedMinuta.objects.order_by("-generation_timestamp").first()
    assert ai_record.minuta_id == new_minuta.id
    assert ai_record.original_command == "Gerar uma minuta de procuração pública completa."
    assert ai_record.parsed_intent == ai_response["parsed_intent"]

    ai_mock = mock_manager.return_value.generate_minuta_from_intent
    ai_mock.assert_awaited_once()
    kwargs = ai_mock.await_args.kwargs
    assert kwargs["command"] == payload["intent"]
    assert kwargs["processo_id"] == processo.id


def test_generate_minuta_requires_authentication(api_client, tenant, user):
    endpoint = _endpoint()
    processo = Processo.objects.create(
        tenant=tenant, tipo_ato="procuracao", status="rascunho", responsavel=user
    )

    client = api_client
    client.credentials(HTTP_X_TENANT_ID=str(tenant.id))

    payload = {
        "intent": "Gerar minuta de procuração.",
        "processo_id": str(processo.id),
    }

    with patch("apps.ai_documents.views.get_ai_service_manager") as mock_manager:
        response = client.post(endpoint, payload, format="json")

    assert response.status_code == 403
    assert response.json()["detail"] == "Authentication credentials were not provided."
    mock_manager.assert_not_called()


def test_generate_minuta_requires_tenant_header(authed_client_no_tenant, processo):
    endpoint = _endpoint()
    payload = {
        "intent": "Gerar minuta de procuração.",
        "processo_id": str(processo.id),
    }

    with patch("apps.ai_documents.views.get_ai_service_manager") as mock_manager:
        response = authed_client_no_tenant.post(endpoint, payload, format="json")

    assert response.status_code == 403
    assert response.json()["detail"] == "Tenant não definido. Envie X-Tenant-ID."
    mock_manager.assert_not_called()


def test_generate_minuta_missing_intent(authed_client, processo):
    endpoint = _endpoint()
    payload = {"processo_id": str(processo.id)}

    with patch("apps.ai_documents.views.get_ai_service_manager") as mock_manager:
        response = authed_client.post(endpoint, payload, format="json")

    assert response.status_code == 400
    error = response.json()["intent"]
    expected = "Campo 'intent' ou 'command' é obrigatório."
    assert (isinstance(error, list) and error == [expected]) or error == expected
    mock_manager.assert_not_called()


def test_generate_minuta_process_not_found(authed_client):
    endpoint = _endpoint()
    ai_response = _make_ai_response()

    with patch("apps.ai_documents.views.get_ai_service_manager") as mock_manager:
        mock_manager.return_value = _build_service_mock(ai_response)
        payload = {
            "intent": "Gerar minuta de procuração.",
            "processo_id": str(uuid4()),
        }
        response = authed_client.post(endpoint, payload, format="json")

    assert response.status_code == 400
    error = response.json()["processo_id"]
    expected = "Processo não encontrado ou não pertence ao tenant."
    assert (isinstance(error, list) and error == [expected]) or error == expected
    assert Minuta.objects.filter(processo_id=payload["processo_id"]).count() == 0

