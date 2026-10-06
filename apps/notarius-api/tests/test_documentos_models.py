import pytest

from apps.documentos.models import Documento, Minuta


@pytest.mark.django_db
def test_documento_str_uses_status_display(tenant, processo):
    doc = Documento.objects.create(
        tenant=tenant,
        processo=processo,
        s3_key="docs/rg1.pdf",
        hash_sha256=b"\x00" * 32,
        mime="application/pdf",
        pages=2,
        status="pronto",
    )
    assert str(doc) == f"Documento {doc.id} - Pronto"


@pytest.mark.django_db
def test_minuta_str_includes_status(tenant, processo, user):
    minuta = Minuta.objects.create(
        tenant=tenant,
        processo=processo,
        versao=3,
        gerada_por="ai",
        status="aprovado",
        corpo_md="## corpo",
        created_by=user,
    )
    assert str(minuta) == f"Minuta {minuta.id} - Aprovado"
