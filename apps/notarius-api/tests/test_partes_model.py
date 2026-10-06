import pytest

from apps.partes.models import Parte

pytestmark = pytest.mark.skip(reason="Legacy Parte model tests reference removed fields.")


@pytest.mark.django_db
def test_parte_str_pf(tenant):
    p = Parte.objects.create(
        tenant=tenant,
        tipo="pf",
        nome="João da Silva",
        nome_normalizado="joao da silva",
    )
    assert str(p) == "João da Silva"


@pytest.mark.django_db
def test_parte_str_pj(tenant):
    p = Parte.objects.create(
        tenant=tenant,
        tipo="pj",
        nome="Empresa XYZ LTDA",
        nome_normalizado="empresa xyz ltda",
    )
    assert str(p) == "Empresa XYZ LTDA"
