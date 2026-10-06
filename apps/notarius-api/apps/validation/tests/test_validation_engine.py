"""
Unit tests for validation engine.
"""

import pytest
from apps.validation.services.validation_engine import ValidationEngine


@pytest.mark.asyncio
async def test_validate_itbi_requirement():
    """Test ITBI validation."""
    engine = ValidationEngine()
    await engine.initialize()
    
    extracted_data = {
        "vendedor": {"nome": "Eduardo", "cpf": "111.222.333-44"},
        "comprador": {"nome": "Marina", "cpf": "555.666.777-88"},
        "imovel": {"matricula": "12345"},
        "financeiro": {"preco": 450000.00}
    }
    
    result = engine._validate_itbi("escritura_compra_venda", extracted_data)
    
    assert result["status"] in ["exigencia", "opcional"]


@pytest.mark.asyncio
async def test_validate_oab_format():
    """Test OAB format validation."""
    engine = ValidationEngine()
    await engine.initialize()
    
    # Valid OAB
    data1 = {"procurador": {"oab": "SP-123456"}}
    result1 = engine._validate_oab(data1)
    assert result1["status"] == "exigencia"
    assert result1["met"] is True
    
    # Invalid OAB
    data2 = {"procurador": {"oab": "SP123456"}}  # Missing dash
    result2 = engine._validate_oab(data2)
    assert result2["status"] in ["bloqueante", "exigencia"]


@pytest.mark.asyncio
async def test_validate_matricula():
    """Test matrícula validation."""
    engine = ValidationEngine()
    await engine.initialize()
    
    # With matrícula
    data1 = {"imovel": {"matricula": "12345"}}
    result1 = engine._validate_matricula(data1)
    assert result1["status"] == "exigencia"
    assert result1["met"] is True
    
    # Without matrícula
    data2 = {"imovel": {}}
    result2 = engine._validate_matricula(data2)
    assert result2["status"] == "exigencia"
    assert result2["met"] is False

