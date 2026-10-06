"""
Unit tests for fee calculator.
"""

import pytest
from decimal import Decimal
from apps.fees.services.fee_calculator import FeeCalculator


def test_calculate_fees_basic():
    """Test basic fee calculation."""
    calculator = FeeCalculator()
    
    # This will return default fees if no rules in DB
    fees = calculator.calculate(
        document_type="escritura_compra_venda",
        uf="SP"
    )
    
    assert "emolumentos" in fees
    assert "frj" in fees
    assert "fundo_estadual" in fees
    assert "itbi" in fees
    assert "total" in fees
    assert isinstance(fees["total"], Decimal)


def test_calculate_fees_with_base_value():
    """Test fee calculation with base value for ITBI."""
    calculator = FeeCalculator()
    
    fees = calculator.calculate(
        document_type="escritura_compra_venda",
        uf="SP",
        base_value=Decimal("450000.00")
    )
    
    assert "itbi" in fees
    assert "total" in fees
    assert fees["total"] >= fees["itbi"]  # Total should include ITBI

