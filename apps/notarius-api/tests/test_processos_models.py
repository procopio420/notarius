import pytest

from apps.partes.models import Parte
from apps.processos.models import Processo, ProcessoParte


@pytest.mark.django_db
def test_processo_str(tenant, user):
    proc = Processo.objects.create(
        tenant=tenant,
        tipo_ato="escritura",
        status="analise",
        responsavel=user,
    )
    assert str(proc) == "escritura (analise)"


@pytest.mark.django_db
def test_processo_parte_str(tenant):
    # cria processo e parte no mesmo tenant
    proc = Processo.objects.create(tenant=tenant, tipo_ato="procuracao", status="rascunho")
    parte = Parte.objects.create(tenant=tenant, tipo="pf", nome="João", nome_normalizado="joao")

    pp = ProcessoParte.objects.create(
        tenant=tenant,
        processo=proc,
        parte=parte,
        papel="outorgante",
    )
    assert str(pp) == f"{proc.id} - {parte.id} (outorgante)"
