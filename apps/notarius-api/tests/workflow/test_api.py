"""
API tests for workflow orchestrator.
"""

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
import pytest


@pytest.fixture
def authenticated_client(api_client):
    """Return an authenticated API client."""
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username="workflow_user",
        email="workflow@example.com",
        password="testpass123",
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.mark.django_db
def test_route_workflow_success(authenticated_client):
    """POST /workflow/route should return a workflow plan."""
    payload = {
        "doc": {
            "tipo_documento": "escritura_compra_venda",
            "especialidade": "tabelionato_notas",
            "uf": "SP",
            "municipio": "São Paulo",
            "partes": [
                {"nome": "Eduardo Rocha", "cpf_cnpj": "333.222.111-00", "papel": "vendedor"},
                {"nome": "Marina Costa", "cpf_cnpj": "555.444.333-22", "papel": "comprador"},
            ],
        },
        "preferencia_online": True,
        "assinatura_disponivel": ["icp_brasil", "e-notariado", "manual"],
        "canais_disponiveis": ["online", "presencial"],
        "anexos": ["itbi"],
    }

    url = reverse("workflow-route")
    response = authenticated_client.post(url, payload, format="json")

    assert response.status_code == 200
    data = response.json()
    assert data["roteamento"]["autoridade"] == "Tabelionato de Notas"
    assert data["assinatura"]["tipo"] == "e-notariado"
    assert "cache_key" in data and len(data["cache_key"]) == 64


@override_settings(ENABLE_ENOTARIADO=False)
@pytest.mark.django_db
def test_route_workflow_respects_feature_flag(authenticated_client):
    """Disabling e-notariado should fall back to presencial/manual flow."""
    payload = {
        "doc": {
            "tipo_documento": "procuracao_ad_judicia",
            "especialidade": "tabelionato_notas",
            "uf": "RJ",
            "municipio": "Niterói",
            "partes": [
                {"nome": "Pedro Mendes", "cpf_cnpj": "987.111.222-33", "papel": "outorgante"},
            ],
        },
        "assinatura_disponivel": ["e-notariado", "icp_brasil", "manual"],
        "canais_disponiveis": ["online", "presencial"],
        "preferencia_online": True,
    }

    url = reverse("workflow-route")
    response = authenticated_client.post(url, payload, format="json")

    assert response.status_code == 200
    data = response.json()
    # With feature disabled, platform should be None and signature should avoid e-notariado
    assert data["roteamento"]["plataforma"] is None
    assert data["assinatura"]["tipo"] != "e-notariado"


@pytest.mark.django_db
def test_get_rulepacks_summary(authenticated_client):
    """GET /workflow/rulepacks should return a summary."""
    url = reverse("workflow-rulepacks")
    response = authenticated_client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert "rules_count" in data
    assert "document_types" in data

