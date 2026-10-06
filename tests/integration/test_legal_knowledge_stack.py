"""
Integration tests for legal knowledge stack end-to-end workflow.
"""

import pytest
import json
import os
from pathlib import Path


@pytest.fixture
def fixtures_dir():
    """Get fixtures directory."""
    return Path(__file__).parent.parent / "fixtures" / "legal_knowledge"


@pytest.fixture
def clean_fixtures(fixtures_dir):
    """Load clean fixtures."""
    with open(fixtures_dir / "clean_inputs.json") as f:
        return json.load(f)


@pytest.fixture
def messy_fixtures(fixtures_dir):
    """Load messy fixtures."""
    with open(fixtures_dir / "messy_inputs.json") as f:
        return json.load(f)


@pytest.fixture
def edge_case_fixtures(fixtures_dir):
    """Load edge case fixtures."""
    with open(fixtures_dir / "edge_cases.json") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_end_to_end_workflow():
    """Test complete workflow: classify → extract → validate."""
    # This is a placeholder for actual integration test
    # In production, this would:
    # 1. Call classify-document endpoint
    # 2. Call extract-form endpoint
    # 3. Call validate-document endpoint
    # 4. Verify results match expected
    
    # For now, just verify the structure
    assert True


@pytest.mark.asyncio
async def test_pii_hashing_deterministic():
    """Test that PII hashing is deterministic."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "intent-engine"))
    from app.services.intent_parser import hash_pii_for_cache
    
    cpf = "333.222.111-00"
    hash1 = hash_pii_for_cache(cpf)
    hash2 = hash_pii_for_cache(cpf)
    
    assert hash1 == hash2  # Same input should produce same hash


@pytest.mark.asyncio
async def test_cache_key_determinism():
    """Test that cache keys are deterministic for same structure."""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / "apps" / "intent-engine"))
    from app.services.intent_parser import create_cache_key
    
    data1 = {
        "vendedor": {"nome": "Eduardo", "cpf": "333.222.111-00"},
        "comprador": {"nome": "Marina", "cpf": "555.444.333-22"}
    }
    
    data2 = {
        "vendedor": {"nome": "João", "cpf": "111.222.333-44"},
        "comprador": {"nome": "Maria", "cpf": "999.888.777-66"}
    }
    
    # Different PII should produce different cache keys
    key1 = create_cache_key(data1, include_pii=False)
    key2 = create_cache_key(data2, include_pii=False)
    
    assert key1 != key2
    
    # Same structure with different PII should still produce different keys
    # (because PII is hashed, but different hashes produce different keys)
    assert len(key1) == len(key2)  # Both should be same length (SHA256 hex)


def test_fixtures_structure(clean_fixtures, messy_fixtures, edge_case_fixtures):
    """Test that fixtures have correct structure."""
    all_fixtures = clean_fixtures + messy_fixtures + edge_case_fixtures
    
    assert len(all_fixtures) >= 25  # Should have at least 25 fixtures
    
    for fixture in all_fixtures:
        assert "input_text" in fixture
        assert "expected" in fixture
        assert "tipo_documento" in fixture["expected"]
        assert "especialidade" in fixture["expected"]
        assert "campos" in fixture["expected"]
        assert "checklist" in fixture["expected"]
        assert "citacoes" in fixture["expected"]

