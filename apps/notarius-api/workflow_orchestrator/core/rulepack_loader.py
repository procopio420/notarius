"""
Rulepack loader and merger.

Loads YAML rulepacks (global + UF-specific) and merges them with
precedence: global < UF.
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


def get_rulepack_path(uf: Optional[str] = None) -> Path:
    """
    Get path to rulepack file.
    
    Args:
        uf: State code (SP, RJ, etc.) or None for global
        
    Returns:
        Path to rulepack file
    """
    # Get base path (project root)
    # Path structure: apps/notarius-api/workflow_orchestrator/core/rulepack_loader.py
    # Go up: rulepack_loader.py -> core -> workflow_orchestrator -> notarius-api -> apps -> project root
    current_file = Path(__file__).resolve()
    # parent (core) -> parent (workflow_orchestrator) -> parent (notarius-api) -> parent (apps) -> project root
    base_path = current_file.parent.parent.parent.parent.parent
    rulepacks_dir = base_path / "rulepacks"
    
    if uf:
        return rulepacks_dir / f"{uf}.yaml"
    else:
        return rulepacks_dir / "global.yaml"


def load_rulepack(uf: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a rulepack YAML file.
    
    Args:
        uf: State code (SP, RJ, etc.) or None for global
        
    Returns:
        Dictionary with rulepack data
    """
    path = get_rulepack_path(uf)
    
    if not path.exists():
        if uf:
            # UF-specific rulepack doesn't exist, return empty dict
            return {}
        else:
            # Global rulepack must exist
            raise FileNotFoundError(f"Global rulepack not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def merge_rulepacks(global_rules: Dict[str, Any], uf_rules: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge rulepacks with precedence: global < UF.
    
    Args:
        global_rules: Global rulepack dictionary
        uf_rules: UF-specific rulepack dictionary
        
    Returns:
        Merged rulepack dictionary
    """
    merged = global_rules.copy()
    
    # Deep merge UF rules over global
    for key, value in uf_rules.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            # Merge nested dictionaries
            merged[key] = merge_dicts(merged[key], value)
        else:
            # UF rule overrides global
            merged[key] = value
    
    return merged


def merge_dicts(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        base: Base dictionary
        override: Override dictionary
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    
    for key, value in override.items():
        if key.endswith("_add") and len(key) > 4:
            # Handle list append operations (e.g., checklist_add)
            base_key = key[:-4]
            if base_key in result and isinstance(result[base_key], list) and isinstance(value, list):
                # Append to existing list
                result[base_key] = result[base_key] + value
            elif base_key not in result:
                # Create new list if base doesn't exist
                result[base_key] = value
            # If base_key exists but is not a list, we'll override it below
            # Don't add the _add key itself
            continue
        elif isinstance(value, dict) and key in result and isinstance(result[key], dict):
            # Recursive merge
            result[key] = merge_dicts(result[key], value)
        else:
            # Override
            result[key] = value
    
    return result


def get_rulepack_for_document(especialidade: str, tipo_documento: str, uf: str) -> Dict[str, Any]:
    """
    Get merged rulepack for a specific document.
    
    Args:
        especialidade: Document specialty
        tipo_documento: Document type
        uf: State code
        
    Returns:
        Merged rulepack rules for the document
    """
    # Load global and UF-specific rulepacks
    global_rules = load_rulepack(None)
    uf_rules = load_rulepack(uf)
    
    # Merge
    merged = merge_rulepacks(global_rules, uf_rules)
    
    # Get rule for this document type
    rule_key = f"{especialidade}.{tipo_documento}"
    return merged.get(rule_key, {})

