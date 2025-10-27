import uuid

import pytest

from apps.integracoes.models import AIChunk, Integracao, Webhook


@pytest.mark.django_db
def test_integracao_str_on_off(tenant):
    i_on = Integracao.objects.create(tenant=tenant, provedor="whatsapp", enabled=True)
    i_off = Integracao.objects.create(tenant=tenant, provedor="assinatura_icp", enabled=False)
    assert str(i_on) == "whatsapp (on)"
    assert str(i_off) == "assinatura_icp (off)"


@pytest.mark.django_db
def test_webhook_str(tenant):
    w = Webhook.objects.create(
        tenant=tenant,
        endpoint="https://example.com/hook",
        secret_hmac="secret",
        eventos=["documento.pronto"],
        enabled=True,
    )
    assert str(w) == "https://example.com/hook"


@pytest.mark.django_db
def test_aichunk_str(tenant):
    sid = uuid.uuid4()
    c = AIChunk.objects.create(
        tenant=tenant,
        source_type="template",
        source_id=sid,
        chunk_idx=7,
        text="lorem ipsum",
        embedding=[],
        meta={},
    )
    assert str(c) == f"template:{sid}#7"
