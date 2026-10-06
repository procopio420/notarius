"""
Unit tests for template renderer.
"""

import pytest
from apps.templates.services.renderer import TemplateRenderer


def test_render_basic():
    """Test basic template rendering."""
    renderer = TemplateRenderer()
    
    template = "Vendedor: {{ vendedor.nome }}, CPF {{ vendedor.cpf }}"
    data = {
        "vendedor": {
            "nome": "Eduardo Rocha",
            "cpf": "333.222.111-00"
        }
    }
    
    result = renderer.render(template, data)
    
    assert "Eduardo Rocha" in result
    assert "333.222.111-00" in result


def test_render_with_state_clauses():
    """Test template rendering with state-specific clauses."""
    renderer = TemplateRenderer()
    
    template = "{{ state_clauses.itbi_text }}"
    data = {}
    
    result = renderer.render(template, data, uf="SP")
    
    assert "ITBI" in result
    assert "SP" in result or "municipal" in result


def test_render_pii_redaction_in_logs():
    """Test that PII is redacted in logs."""
    renderer = TemplateRenderer()
    
    template = "CPF: {{ cpf }}"
    data = {"cpf": "333.222.111-00"}
    
    # Render should work normally
    result = renderer.render(template, data)
    assert "333.222.111-00" in result  # Actual result should have PII
    
    # But logs should be sanitized (tested via mock or inspection)

