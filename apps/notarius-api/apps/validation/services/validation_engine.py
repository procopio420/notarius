"""
Validation engine service for legal document requirements.
"""

import logging
import re
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# Ensure packages directory is in Python path
# This is a safeguard in case Django hasn't loaded it yet
if '/packages' not in sys.path and os.path.exists('/packages'):
    sys.path.insert(0, '/packages')
elif not any('packages' in p for p in sys.path):
    # Try to find packages directory relative to this file
    current_file = Path(__file__).resolve()
    # Go up: services -> validation -> apps -> notarius-api -> project root
    project_root = current_file.parent.parent.parent.parent.parent
    packages_path = project_root / 'packages'
    if packages_path.exists():
        sys.path.insert(0, str(packages_path))

# Import http_client with fallback for build time
try:
    from packages.core.http_client import get_http_client
except ImportError:
    # During Docker build, packages might not be available yet
    # Create a mock function that will be replaced at runtime
    def get_http_client():
        """Mock http_client for build time. Will be replaced at runtime."""
        raise RuntimeError("HTTP client not available during build. This should only be called at runtime.")

logger = logging.getLogger(__name__)


class ValidationEngine:
    """Validates legal documents against applicable rules."""
    
    def __init__(self):
        self.http_client = None
        self.lexnode_url = None
    
    async def initialize(self):
        """Initialize HTTP client."""
        import os
        try:
            self.http_client = get_http_client()
        except RuntimeError as e:
            # During build, http_client might not be available
            # This is OK - it will be initialized at runtime
            if "build" in str(e).lower() or "not available" in str(e).lower():
                logger.warning("HTTP client not available during build. Will initialize at runtime.")
                self.http_client = None
            else:
                raise
        self.lexnode_url = os.getenv("LEXNODE_URL", "http://lexnode-api:8000")
    
    async def validate(
        self,
        document_type: str,
        extracted_data: Dict,
        uf: Optional[str] = None
    ) -> Dict:
        """
        Validate document against legal rules.
        
        Args:
            document_type: Document type (e.g., 'escritura_compra_venda')
            extracted_data: Extracted form data
            uf: State jurisdiction (optional)
            
        Returns:
            Dict with exigencias, bloqueantes, opcionais, citacoes
        """
        logger.info(f"Validating {document_type} for UF={uf}")
        
        if not self.http_client:
            await self.initialize()
        
        # Get applicable rules from legal_knowledge
        rules = await self._get_rules(document_type, uf)
        
        # Apply validation rules
        exigencias = []
        bloqueantes = []
        opcionais = []
        citacoes = []
        
        for rule in rules.get("rules", []):
            checklist_item = rule.get("checklist_item")
            citation = rule.get("citation")
            
            if citation:
                citacoes.append(citation)
            
            # Apply rule-specific validations
            validation_result = self._apply_rule_validation(
                rule, document_type, extracted_data
            )
            
            if validation_result["status"] == "bloqueante":
                bloqueantes.append({
                    "item": checklist_item,
                    "citation": citation,
                    "reason": validation_result["reason"]
                })
            elif validation_result["status"] == "exigencia":
                exigencias.append({
                    "item": checklist_item,
                    "citation": citation,
                    "met": validation_result.get("met", False)
                })
            elif validation_result["status"] == "opcional":
                opcionais.append({
                    "item": checklist_item,
                    "citation": citation
                })
        
        # Add checklist items without validation results as exigencias
        for item in rules.get("checklist", []):
            if not any(e.get("item") == item for e in exigencias):
                exigencias.append({
                    "item": item,
                    "citation": rules.get("citacoes", [])[0] if rules.get("citacoes") else None,
                    "met": False
                })
        
        return {
            "exigencias": exigencias,
            "bloqueantes": bloqueantes,
            "opcionais": opcionais,
            "citacoes": list(set(citacoes))
        }
    
    async def _get_rules(self, document_type: str, uf: Optional[str]) -> Dict:
        """Get applicable rules from lexnode-api."""
        try:
            url = f"{self.lexnode_url}/api/v1/rules"
            params = {"doctype": document_type}
            if uf:
                params["uf"] = uf
            
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get rules: {e}")
            return {"rules": [], "checklist": [], "citacoes": []}
    
    def _apply_rule_validation(
        self,
        rule: Dict,
        document_type: str,
        extracted_data: Dict
    ) -> Dict:
        """Apply specific validation rule."""
        checklist_item = rule.get("checklist_item", "").lower()
        content = rule.get("content", "").lower()
        
        # ITBI check
        if "itbi" in checklist_item or "itbi" in content:
            return self._validate_itbi(document_type, extracted_data)
        
        # Certidão validity check
        if "certidão" in checklist_item or "certidao" in checklist_item:
            if "<=30" in checklist_item or "30 dias" in checklist_item:
                return self._validate_certidao_validity(extracted_data)
        
        # Habite-se check
        if "habite-se" in checklist_item or "habite se" in checklist_item:
            return self._validate_habite_se(extracted_data)
        
        # OAB format check
        if "oab" in checklist_item:
            return self._validate_oab(extracted_data)
        
        # Matrícula format check
        if "matrícula" in checklist_item or "matricula" in checklist_item:
            return self._validate_matricula(extracted_data)
        
        # Default: treat as exigencia
        return {
            "status": "exigencia",
            "met": False
        }
    
    def _validate_itbi(self, document_type: str, extracted_data: Dict) -> Dict:
        """Validate ITBI requirement."""
        # ITBI is required for compra/venda imóvel
        if document_type in ["escritura_compra_venda", "registro_compra_venda_ri"]:
            # Check if ITBI is mentioned in data
            data_str = str(extracted_data).lower()
            if "itbi" in data_str and ("quitado" in data_str or "pago" in data_str):
                return {"status": "exigencia", "met": True}
            else:
                return {"status": "exigencia", "met": False}
        return {"status": "opcional"}
    
    def _validate_certidao_validity(self, extracted_data: Dict) -> Dict:
        """Validate certidão is within 30 days."""
        # This would check a certidão date if provided
        # For now, assume it's an exigencia
        return {"status": "exigencia", "met": False}
    
    def _validate_habite_se(self, extracted_data: Dict) -> Dict:
        """Validate habite-se requirement."""
        if extracted_data.get("habite_se"):
            return {"status": "exigencia", "met": True}
        return {"status": "exigencia", "met": False}
    
    def _validate_oab(self, extracted_data: Dict) -> Dict:
        """Validate OAB format."""
        # Check for OAB in nested structures
        def find_oab(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if 'oab' in key.lower():
                        if value and isinstance(value, str):
                            # Check format: UF-XXXXXX
                            if re.match(r'^[A-Z]{2}-\d+$', value):
                                return True
                            return False
                    elif isinstance(value, (dict, list)):
                        result = find_oab(value)
                        if result is not None:
                            return result
            elif isinstance(data, list):
                for item in data:
                    result = find_oab(item)
                    if result is not None:
                        return result
            return None
        
        import re
        oab_valid = find_oab(extracted_data)
        if oab_valid is True:
            return {"status": "exigencia", "met": True}
        elif oab_valid is False:
            return {"status": "bloqueante", "reason": "OAB format invalid"}
        return {"status": "opcional"}
    
    def _validate_matricula(self, extracted_data: Dict) -> Dict:
        """Validate matrícula format."""
        # Check for matrícula in nested structures
        def find_matricula(data):
            if isinstance(data, dict):
                for key, value in data.items():
                    if 'matricula' in key.lower():
                        if value:
                            return True
                    elif isinstance(value, (dict, list)):
                        if find_matricula(value):
                            return True
            elif isinstance(data, list):
                for item in data:
                    if find_matricula(item):
                        return True
            return False
        
        if find_matricula(extracted_data):
            return {"status": "exigencia", "met": True}
        return {"status": "exigencia", "met": False}

