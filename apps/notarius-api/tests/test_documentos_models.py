import pytest

from apps.documentos.models import Checklist, Documento, Minuta


@pytest.mark.django_db
def test_documento_str(tenant, processo):
    doc = Documento.objects.create(
        tenant=tenant,
        processo=processo,
        tipo="rg",
        s3_key="docs/rg1.pdf",
        hash_sha256=b"\x00" * 32,
        status="novo",
    )
    assert str(doc) == "docs/rg1.pdf"


@pytest.mark.django_db
def test_minuta_str(tenant, processo, user):
    m = Minuta.objects.create(
        tenant=tenant,
        processo=processo,
        versao=3,
        gerada_por="humano",
        corpo_md="## corpo",
        created_by=user,
    )
    assert str(m) == f"Minuta v3 ({processo.id})"


@pytest.mark.django_db
def test_checklist_str(tenant, processo):
    c = Checklist.objects.create(
        tenant=tenant,
        processo=processo,
        item="Conferir RG",
        ordem=1,
        done_by=None,
    )
    assert str(c) == "Conferir RG"
