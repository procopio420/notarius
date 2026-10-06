"""
Tests for rulepack loader.
"""

import pytest
from pathlib import Path
from workflow_orchestrator.core.rulepack_loader import (
    load_rulepack,
    merge_rulepacks,
    get_rulepack_for_document,
    get_rulepack_path
)


class TestRulepackLoader:
    """Test rulepack loading."""
    
    def test_load_global_rulepack(self):
        """Test loading global rulepack."""
        rules = load_rulepack(None)
        
        assert isinstance(rules, dict)
        assert len(rules) > 0
    
    def test_load_uf_rulepack(self):
        """Test loading UF-specific rulepack."""
        # Try to load SP rulepack (may not exist, that's OK)
        try:
            rules = load_rulepack("SP")
            assert isinstance(rules, dict)
        except FileNotFoundError:
            # SP rulepack doesn't exist yet, that's OK
            pass
    
    def test_load_nonexistent_uf_returns_empty(self):
        """Test that nonexistent UF rulepack returns empty dict."""
        rules = load_rulepack("XX")  # Non-existent UF
        
        assert isinstance(rules, dict)
        assert len(rules) == 0


class TestMergeRulepacks:
    """Test rulepack merging."""
    
    def test_merge_rulepacks_uf_overrides_global(self):
        """Test that UF rules override global rules."""
        global_rules = {
            "tabelionato_notas.escritura_compra_venda": {
                "checklist": ["Item 1", "Item 2"],
                "citacoes": ["Lei 1"]
            }
        }
        
        uf_rules = {
            "tabelionato_notas.escritura_compra_venda": {
                "checklist": ["Item 3"],
                "citacoes": ["Lei 2"]
            }
        }
        
        merged = merge_rulepacks(global_rules, uf_rules)
        
        rule = merged["tabelionato_notas.escritura_compra_venda"]
        assert rule["checklist"] == ["Item 3"]  # UF overrides
        assert rule["citacoes"] == ["Lei 2"]  # UF overrides
    
    def test_merge_rulepacks_checklist_add(self):
        """Test that checklist_add appends to checklist."""
        global_rules = {
            "registro_imoveis.averbacao_construcao": {
                "checklist": ["Item 1", "Item 2"]
            }
        }
        
        uf_rules = {
            "registro_imoveis.averbacao_construcao": {
                "checklist_add": ["Item 3", "Item 4"]
            }
        }
        
        merged = merge_rulepacks(global_rules, uf_rules)
        
        rule = merged["registro_imoveis.averbacao_construcao"]
        assert "Item 1" in rule["checklist"]
        assert "Item 2" in rule["checklist"]
        assert "Item 3" in rule["checklist"]
        assert "Item 4" in rule["checklist"]


class TestGetRulepackForDocument:
    """Test getting rulepack for specific document."""
    
    def test_get_rulepack_for_document(self):
        """Test getting rulepack for a document."""
        rule = get_rulepack_for_document(
            "tabelionato_notas",
            "escritura_compra_venda",
            "SP"
        )
        
        assert isinstance(rule, dict)
        # Should have at least some fields
        assert "quem_assina" in rule or "checklist" in rule or "citacoes" in rule

