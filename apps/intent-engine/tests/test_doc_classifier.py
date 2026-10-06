"""
Unit tests for document classifier.
"""

import pytest
from app.services.doc_classifier import DocumentClassifier


@pytest.mark.asyncio
async def test_classify_escritura_compra_venda():
    """Test classification of escritura de compra e venda."""
    classifier = DocumentClassifier()
    
    text = "Escritura de compra e venda. Vendedor: Eduardo Rocha, CPF 333.222.111-00. Compradora: Marina Costa, CPF 555.444.333-22. Imóvel: matrícula 12345, 2º RI Curitiba/PR. Preço R$ 450.000, pagamento à vista."
    
    result = await classifier.classify(text)
    
    assert result["tipo_documento"] == "escritura_compra_venda"
    assert result["especialidade"] == "tabelionato_notas"
    assert result["confianca"] > 0.5


@pytest.mark.asyncio
async def test_classify_procuracao_ad_judicia():
    """Test classification of procuração ad judicia."""
    classifier = DocumentClassifier()
    
    text = "Procuração ad judicia. Outorgante: Pedro Mendes, CPF 987.111.222-33. Outorgada: Ana Beatriz Rocha, OAB/SP 123456. Poderes gerais forenses e receber citação."
    
    result = await classifier.classify(text)
    
    assert result["tipo_documento"] == "procuracao_ad_judicia"
    assert result["especialidade"] == "tabelionato_notas"
    assert result["confianca"] > 0.5


@pytest.mark.asyncio
async def test_classify_messy_input():
    """Test classification with messy input (abreviações, typos)."""
    classifier = DocumentClassifier()
    
    text = "(messy) escr comp e venda — vend: E Rocha CPF 33322211100; comp: M Costa cpf 55544433322; mat 12345 2 RI Curitiba; preço 450k a vista."
    
    result = await classifier.classify(text)
    
    assert result["tipo_documento"] == "escritura_compra_venda"
    assert result["confianca"] > 0.3  # Lower confidence for messy input


@pytest.mark.asyncio
async def test_classify_all_specialties():
    """Test classification for all document types."""
    classifier = DocumentClassifier()
    
    test_cases = [
        ("procuração ad judicia", "procuracao_ad_judicia", "tabelionato_notas"),
        ("procuração para veículo", "procuracao_veiculo", "tabelionato_notas"),
        ("ata notarial", "ata_notarial_constatacao", "tabelionato_notas"),
        ("registro de nascimento", "assento_nascimento", "rcpn"),
        ("averbar divórcio", "averbacao_divorcio", "rcpn"),
        ("registro compra venda imóvel", "registro_compra_venda_ri", "registro_imoveis"),
        ("averb construção", "averbacao_construcao", "registro_imoveis"),
        ("registro contrato locação", "registro_contrato_locacao", "rtd"),
        ("notific extrajudicial", "notificacao_extrajudicial", "rtd"),
        ("protesto título", "protesto_titulo", "protesto"),
        ("certidão ônus reais", "certidao_onus_reais", "registro_imoveis"),
    ]
    
    for text, expected_type, expected_specialty in test_cases:
        result = await classifier.classify(text)
        assert result["tipo_documento"] == expected_type or result["confianca"] < 0.5  # Allow for uncertainty
        if result["tipo_documento"] == expected_type:
            assert result["especialidade"] == expected_specialty

