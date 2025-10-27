import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_financeiro_item_crud(authed_client, processo):
    url = reverse("financeiro-item-list")
    payload = {
        "processo": str(processo.id),
        "tabela_uf": "SP",
        "descricao": "Emolumentos escritura",
        "valor_cents": 12345,
        "tributos": {"iss": 500},
    }
    r = authed_client.post(url, payload, format="json")
    assert r.status_code == 201, r.content
    item_id = r.json()["id"]

    r = authed_client.get(url, {"processo": str(processo.id)})
    assert r.status_code == 200

    r = authed_client.patch(
        reverse("financeiro-item-detail", args=[item_id]), {"valor_cents": 23456}, format="json"
    )
    assert r.status_code == 200
    assert r.json()["valor_cents"] == 23456

    r = authed_client.delete(reverse("financeiro-item-detail", args=[item_id]))
    assert r.status_code in (204, 200)
