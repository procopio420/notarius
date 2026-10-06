"""
Tests for PII utilities.
"""

import pytest
from workflow_orchestrator.utils.pii import hash_pii, redact_pii_in_logs, generate_cache_key
from workflow_orchestrator.models.contracts import DocumentoBasico, Parte


class TestHashPII:
    """Test PII hashing."""
    
    def test_hash_pii_produces_stable_hash(self):
        """Test that same input produces same hash."""
        value = "123.456.789-00"
        hash1 = hash_pii(value)
        hash2 = hash_pii(value)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_hash_pii_different_values_produce_different_hashes(self):
        """Test that different inputs produce different hashes."""
        hash1 = hash_pii("123.456.789-00")
        hash2 = hash_pii("987.654.321-00")
        
        assert hash1 != hash2
    
    def test_hash_pii_handles_empty_string(self):
        """Test that empty string returns empty string."""
        assert hash_pii("") == ""
    
    def test_hash_pii_normalizes_input(self):
        """Test that formatting is normalized."""
        hash1 = hash_pii("123.456.789-00")
        hash2 = hash_pii("12345678900")
        
        assert hash1 == hash2


class TestRedactPIIInLogs:
    """Test PII redaction in logs."""
    
    def test_redact_cpf_cnpj(self):
        """Test that CPF/CNPJ is redacted."""
        data = {
            "cpf_cnpj": "123.456.789-00",
            "nome": "João Silva",
            "other_field": "value"
        }
        
        redacted = redact_pii_in_logs(data)
        
        assert redacted["cpf_cnpj"] == "[REDACTED]"
        assert redacted["nome"] == "[REDACTED]"
        assert redacted["other_field"] == "value"
    
    def test_redact_nested_dicts(self):
        """Test that nested dictionaries are redacted."""
        data = {
            "parte": {
                "nome": "João",
                "cpf": "123.456.789-00"
            }
        }
        
        redacted = redact_pii_in_logs(data)
        
        assert redacted["parte"]["nome"] == "[REDACTED]"
        assert redacted["parte"]["cpf"] == "[REDACTED]"
    
    def test_redact_lists(self):
        """Test that lists with PII are redacted."""
        data = {
            "partes": [
                {"nome": "João", "cpf": "123.456.789-00"},
                {"nome": "Maria", "cpf": "987.654.321-00"}
            ]
        }
        
        redacted = redact_pii_in_logs(data)
        
        assert len(redacted["partes"]) == 2
        assert redacted["partes"][0]["nome"] == "[REDACTED]"
        assert redacted["partes"][0]["cpf"] == "[REDACTED]"


class TestGenerateCacheKey:
    """Test cache key generation."""
    
    def test_cache_key_is_stable(self):
        """Test that same input produces same cache key."""
        doc = DocumentoBasico(
            tipo_documento="escritura_compra_venda",
            especialidade="tabelionato_notas",
            uf="SP",
            municipio="São Paulo",
            partes=[
                Parte(nome="João", cpf_cnpj="123.456.789-00", papel="vendedor")
            ]
        )
        anexos = ["itbi"]
        
        key1 = generate_cache_key(doc, anexos)
        key2 = generate_cache_key(doc, anexos)
        
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex length
    
    def test_cache_key_different_docs_produce_different_keys(self):
        """Test that different documents produce different keys."""
        doc1 = DocumentoBasico(
            tipo_documento="escritura_compra_venda",
            especialidade="tabelionato_notas",
            uf="SP",
            partes=[Parte(cpf_cnpj="123.456.789-00", papel="vendedor")]
        )
        doc2 = DocumentoBasico(
            tipo_documento="procuracao",
            especialidade="tabelionato_notas",
            uf="SP",
            partes=[Parte(cpf_cnpj="123.456.789-00", papel="vendedor")]
        )
        
        key1 = generate_cache_key(doc1, [])
        key2 = generate_cache_key(doc2, [])
        
        assert key1 != key2
    
    def test_cache_key_includes_anexos(self):
        """Test that anexos are included in cache key."""
        doc = DocumentoBasico(
            tipo_documento="escritura_compra_venda",
            especialidade="tabelionato_notas",
            uf="SP",
            partes=[]
        )
        
        key1 = generate_cache_key(doc, ["itbi"])
        key2 = generate_cache_key(doc, ["itbi", "habite_se"])
        
        assert key1 != key2

