import pytest
from django.contrib import admin
from django.test import RequestFactory

from apps.documentos.admin import DocumentoAdmin
from apps.documentos.models import Documento


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.mark.django_db
def test_atualizar_busca_ocr_calls_message_user_and_iterates(
    rf, superuser, tenant, processo, monkeypatch
):
    # 2 documentos para exercitar o 'for doc in queryset: pass'
    d1 = Documento.objects.create(
        tenant=tenant,
        processo=processo,
        tipo="rg",
        s3_key="docs/rg1.pdf",
        hash_sha256=b"\x00" * 32,
        status="novo",
    )
    d2 = Documento.objects.create(
        tenant=tenant,
        processo=processo,
        tipo="cpf",
        s3_key="docs/cpf1.pdf",
        hash_sha256=b"\x01" * 32,
        status="novo",
    )

    req = rf.post("/admin/documentos/documento/")
    req.user = superuser
    req.tenant = tenant  # BaseTenantAdmin usa isso em outros métodos

    admin_instance = DocumentoAdmin(Documento, admin.site)
    qs = Documento.objects.filter(pk__in=[d1.pk, d2.pk])

    # Captura a mensagem enviada pelo admin
    captured = {}

    def fake_message_user(self, request, message, level=None, extra_tags="", fail_silently=False):  # noqa: ARG001, PLR0913
        captured["message"] = message
        captured["level"] = level

    monkeypatch.setattr(
        admin_instance,
        "message_user",
        fake_message_user.__get__(admin_instance, DocumentoAdmin),  # bind na instância
    )

    # Act
    admin_instance.atualizar_busca_ocr(req, qs)

    # Assert: mensagem contém a contagem correta do queryset
    assert captured["message"] == "Solicitada atualização de FTS para 2 documento(s)."
