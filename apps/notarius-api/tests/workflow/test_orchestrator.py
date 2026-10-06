"""
Tests for workflow orchestrator.
"""

import json
import pytest
from pathlib import Path
from workflow_orchestrator.models.contracts import WorkflowInput
from workflow_orchestrator.core.orchestrator import plan_from_input
from workflow_orchestrator.utils.pii import redact_pii_in_logs


def load_fixtures():
    """Load test fixtures from JSONL file."""
    fixtures_path = Path(__file__).parent / "fixtures.jsonl"
    
    fixtures = []
    with open(fixtures_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                fixtures.append(json.loads(line))
    
    return fixtures


class TestOrchestrator:
    """Test workflow orchestrator."""
    
    def test_plan_from_input_returns_workflow_plan(self):
        """Test that plan_from_input returns a valid WorkflowPlan."""
        input_data = WorkflowInput(
            doc={
                "tipo_documento": "escritura_compra_venda",
                "especialidade": "tabelionato_notas",
                "uf": "SP",
                "municipio": "São Paulo",
                "partes": []
            }
        )
        
        plan = plan_from_input(input_data)
        
        assert plan.roteamento is not None
        assert plan.assinatura is not None
        assert plan.cache_key is not None
        assert len(plan.cache_key) == 64  # SHA256 hex length
    
    def test_plan_from_input_has_stable_cache_key(self):
        """Test that same input produces same cache key."""
        input_data = WorkflowInput(
            doc={
                "tipo_documento": "escritura_compra_venda",
                "especialidade": "tabelionato_notas",
                "uf": "SP",
                "municipio": "São Paulo",
                "partes": [
                    {"cpf_cnpj": "123.456.789-00", "papel": "vendedor"}
                ]
            },
            anexos=["itbi"]
        )
        
        plan1 = plan_from_input(input_data)
        plan2 = plan_from_input(input_data)
        
        assert plan1.cache_key == plan2.cache_key


class TestFixtures:
    """Test all fixtures from fixtures.jsonl."""
    
    @pytest.mark.parametrize("fixture", load_fixtures())
    def test_fixture(self, fixture):
        """Test a single fixture."""
        input_data = WorkflowInput(**fixture["input"])
        expected = fixture["expected"]
        
        # Generate plan
        plan = plan_from_input(input_data)
        
        # Validate roteamento
        assert plan.roteamento.autoridade == expected["roteamento"]["autoridade"]
        assert plan.roteamento.plataforma == expected["roteamento"].get("plataforma")
        assert plan.roteamento.modo == expected["roteamento"]["modo"]
        
        # Validate assinatura
        assert plan.assinatura.tipo == expected["assinatura"]["tipo"]
        assert set(plan.assinatura.quem_assina) == set(expected["assinatura"]["quem_assina"])
        
        if "videoconferencia" in expected["assinatura"]:
            assert plan.assinatura.videoconferencia == expected["assinatura"]["videoconferencia"]
        
        # Validate checklist contains expected items
        if "checklist_contains" in expected:
            for item in expected["checklist_contains"]:
                # Check if any checklist item contains this text (case-insensitive)
                checklist_lower = [c.lower() for c in plan.checklist]
                assert any(item.lower() in c for c in checklist_lower), \
                    f"Expected '{item}' not found in checklist: {plan.checklist}"
        
        # Validate citacoes contains expected items
        if "citacoes_contains" in expected:
            for citation in expected["citacoes_contains"]:
                citacoes_lower = [c.lower() for c in plan.citacoes]
                assert any(citation.lower() in c for c in citacoes_lower), \
                    f"Expected '{citation}' not found in citacoes: {plan.citacoes}"
        
        # Validate fees_hint contains expected items
        if "fees_hint_contains" in expected:
            for fee in expected["fees_hint_contains"]:
                fees_lower = [f.lower() for f in plan.fees_hint]
                assert any(fee.lower() in f for f in fees_lower), \
                    f"Expected '{fee}' not found in fees_hint: {plan.fees_hint}"
        
        # Validate cache_key is present
        assert plan.cache_key is not None
        assert len(plan.cache_key) == 64


class TestPrivacy:
    """Test that no PII appears in logs."""
    
    def test_no_pii_in_logs(self, caplog):
        """Test that logs don't contain PII."""
        import logging
        logger = logging.getLogger("workflow_orchestrator.core.orchestrator")
        
        input_data = WorkflowInput(
            doc={
                "tipo_documento": "escritura_compra_venda",
                "especialidade": "tabelionato_notas",
                "uf": "SP",
                "municipio": "São Paulo",
                "partes": [
                    {"nome": "João Silva", "cpf_cnpj": "123.456.789-00", "papel": "vendedor"}
                ]
            }
        )
        
        with caplog.at_level(logging.INFO):
            plan_from_input(input_data)
        
        # Check that no PII appears in logs
        log_text = "\n".join(caplog.text)
        assert "123.456.789-00" not in log_text
        assert "João Silva" not in log_text
        assert "12345678900" not in log_text

