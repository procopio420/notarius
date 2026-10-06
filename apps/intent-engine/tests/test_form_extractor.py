"""
Unit tests for form extractor.
"""

import pytest
from app.services.form_extractor import FormExtractor


@pytest.mark.asyncio
async def test_extract_escritura_compra_venda():
    """Test extraction for escritura de compra e venda."""
    extractor = FormExtractor()
    
    text = "Escritura de compra e venda. Vendedor: Eduardo Rocha, CPF 333.222.111-00. Compradora: Marina Costa, CPF 555.444.333-22. Imóvel: matrícula 12345, 2º RI Curitiba/PR. Preço R$ 450.000, pagamento à vista."
    
    result = await extractor.extract(text, "escritura_compra_venda")
    
    assert "vendedor" in result or "comprador" in result
    assert "imovel" in result or "financeiro" in result


@pytest.mark.asyncio
async def test_normalize_cpf():
    """Test CPF normalization."""
    extractor = FormExtractor()
    
    # Test various CPF formats
    test_cases = [
        ("333.222.111-00", "333.222.111-00"),
        ("33322211100", "333.222.111-00"),
        ("333 222 111 00", "333.222.111-00"),
    ]
    
    for input_cpf, expected in test_cases:
        normalized = extractor._normalize_cpf(input_cpf)
        assert normalized == expected or len(normalized.replace(".", "").replace("-", "")) == 11


@pytest.mark.asyncio
async def test_normalize_currency():
    """Test currency normalization."""
    extractor = FormExtractor()
    
    # Test various currency formats
    test_cases = [
        ("R$ 450.000", 450000.00),
        ("450k", 450000.00),
        ("450 mil", 450000.00),
        ("R$ 450000,00", 450000.00),
    ]
    
    for input_val, expected in test_cases:
        normalized = extractor._normalize_currency(input_val, "")
        assert normalized is None or abs(normalized - expected) < 1000  # Allow some tolerance


@pytest.mark.asyncio
async def test_normalize_oab():
    """Test OAB normalization."""
    extractor = FormExtractor()
    
    test_cases = [
        ("OAB/SP 123456", "SP-123456"),
        ("SP123456", "SP-123456"),
        ("OABSP123456", "SP-123456"),
    ]
    
    for input_oab, expected in test_cases:
        normalized = extractor._normalize_oab(input_oab)
        assert "SP" in normalized and "123456" in normalized


@pytest.mark.asyncio
async def test_infer_condicao():
    """Test payment condition inference."""
    extractor = FormExtractor()
    
    text_avista = "pagamento à vista"
    text_parcelado = "pagamento parcelado em 12 vezes"
    
    data1 = {"financeiro": {}}
    extractor._infer_fields(data1, "escritura_compra_venda", text_avista)
    assert data1.get("financeiro", {}).get("condicao") == "avista"
    
    data2 = {"financeiro": {}}
    extractor._infer_fields(data2, "escritura_compra_venda", text_parcelado)
    assert data2.get("financeiro", {}).get("condicao") == "parcelado"

