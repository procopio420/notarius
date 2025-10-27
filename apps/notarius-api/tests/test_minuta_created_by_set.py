# tests/test_minuta_created_by_set.py
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_minuta_perform_create_sets_created_by(authed_client, processo, user):
    payload = {
        "processo": str(processo.id),
        "versao": 1,
        "gerada_por": "humano",
        "corpo_md": "## corpo",
    }
    res = authed_client.post(reverse("minuta-list"), payload, format="json")
    assert res.status_code == 201, res.content
    body = res.json()

    # created_by deve ser exatamente o request.user
    # dependendo do serializer, created_by pode vir como ID ou objeto nested; assumindo ID:
    assert str(body["created_by"]) in {str(user.id), user.id}  # cobre UUID/str
