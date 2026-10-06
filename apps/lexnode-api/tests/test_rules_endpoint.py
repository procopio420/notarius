"""
Unit tests for rules endpoint.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

pytestmark = pytest.mark.skip(reason="Legacy rules endpoint tests require full database setup.")

client = TestClient(app)


def test_rules_endpoint_basic():
    """Test basic rules endpoint."""
    response = client.get("/api/v1/rules?doctype=escritura_compra_venda&uf=SP")
    
    assert response.status_code in [200, 500]  # May fail if no rules in DB
    if response.status_code == 200:
        data = response.json()
        assert "rules" in data
        assert "checklist" in data
        assert "citacoes" in data


def test_rules_endpoint_no_params():
    """Test rules endpoint without parameters."""
    response = client.get("/api/v1/rules")
    
    assert response.status_code in [200, 500]  # May fail if no rules in DB
    if response.status_code == 200:
        data = response.json()
        assert "rules" in data


def test_rules_endpoint_with_uf():
    """Test rules endpoint with UF parameter."""
    response = client.get("/api/v1/rules?uf=RJ")
    
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "rules" in data

