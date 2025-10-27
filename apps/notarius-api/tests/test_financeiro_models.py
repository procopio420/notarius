import pytest

from apps.financeiro.models import FinanceiroItem


@pytest.mark.django_db
def test_financeiroitem_str_basic(tenant, processo):
    item = FinanceiroItem.objects.create(
        tenant=tenant,
        processo=processo,
        tabela_uf="SP",
        descricao="Emolumentos escritura",
        valor_cents=12345,  # 123,45
        tributos={"iss": 500},
    )
    assert str(item) == "Emolumentos escritura - 123.45"


@pytest.mark.django_db
def test_financeiroitem_str_zero_and_negative(tenant, processo):
    zero = FinanceiroItem.objects.create(
        tenant=tenant, processo=processo, tabela_uf="SP", descricao="Isento", valor_cents=0
    )
    assert str(zero) == "Isento - 0.00"

    negativo = FinanceiroItem.objects.create(
        tenant=tenant,
        processo=processo,
        tabela_uf="SP",
        descricao="Ajuste",
        valor_cents=-50,  # -0,50
    )
    assert str(negativo) == "Ajuste - -0.50"
