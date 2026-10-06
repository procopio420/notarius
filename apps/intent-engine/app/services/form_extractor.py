"""
Form extractor service for extracting structured data from free-text.
"""

import json
import re
import logging
import hashlib
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal

from .llm import get_llm_service
from ..schemas import (
    EscrituraCompraVendaSchema,
    ProcuracaoAdJudiciaSchema,
    ProcuracaoVeiculoSchema,
    AtaNotarialConstatacaoSchema,
    AssentoNascimentoSchema,
    AverbacaoDivorcioSchema,
    RegistroCompraVendaRISchema,
    AverbacaoConstrucaoSchema,
    CertidaoOnusReaisSchema,
    RegistroContratoLocacaoSchema,
    NotificacaoExtrajudicialSchema,
    ProtestoTituloSchema,
)

logger = logging.getLogger(__name__)


def hash_pii_for_cache(value: str, salt: Optional[str] = None) -> str:
    """Hash PII value for caching."""
    if salt is None:
        salt = os.getenv("PII_HASH_SALT", "default_salt_change_in_production")
    return hashlib.pbkdf2_hmac(
        'sha256',
        value.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()


class FormExtractor:
    """Extracts structured form data from free-text input."""
    
    # Schema mapping by document type
    SCHEMA_MAP = {
        "escritura_compra_venda": EscrituraCompraVendaSchema,
        "procuracao_ad_judicia": ProcuracaoAdJudiciaSchema,
        "procuracao_veiculo": ProcuracaoVeiculoSchema,
        "ata_notarial_constatacao": AtaNotarialConstatacaoSchema,
        "assento_nascimento": AssentoNascimentoSchema,
        "averbacao_divorcio": AverbacaoDivorcioSchema,
        "registro_compra_venda_ri": RegistroCompraVendaRISchema,
        "averbacao_construcao": AverbacaoConstrucaoSchema,
        "certidao_onus_reais": CertidaoOnusReaisSchema,
        "registro_contrato_locacao": RegistroContratoLocacaoSchema,
        "notificacao_extrajudicial": NotificacaoExtrajudicialSchema,
        "protesto_titulo": ProtestoTituloSchema,
    }
    
    def __init__(self):
        self.llm_service = None
    
    async def extract(
        self,
        text: str,
        document_type: str,
        context: Optional[Dict] = None,
        tenant_id: Optional[str] = None
    ) -> Dict:
        """
        Extract structured form data from text.
        
        Args:
            text: Free-text input
            document_type: Document type (e.g., 'escritura_compra_venda')
            context: Additional context
            tenant_id: Tenant ID
            
        Returns:
            Extracted and normalized form data
        """
        logger.info(f"Extracting form data for {document_type}")
        
        # Get schema class
        schema_class = self.SCHEMA_MAP.get(document_type)
        if not schema_class:
            raise ValueError(f"Unknown document type: {document_type}")
        
        # Use LLM to extract structured data
        extracted_data = await self._extract_with_llm(
            text, document_type, context, tenant_id
        )
        
        # Normalize extracted data
        normalized_data = self._normalize_data(extracted_data, document_type, text)
        
        # Validate against schema
        try:
            validated = schema_class(**normalized_data)
            result = validated.dict(exclude_none=True)
            
            # Hash PII in result for logging (not in actual return)
            if logger.isEnabledFor(logging.DEBUG):
                result_for_log = self._hash_pii_in_dict(result.copy())
                logger.debug(f"Extracted form data (PII hashed): {result_for_log}")
            
            return result
        except Exception as e:
            logger.warning(f"Schema validation failed, returning raw data: {e}")
            return normalized_data
    
    def _hash_pii_in_dict(self, data: Dict) -> Dict:
        """Hash PII fields in dict for logging."""
        pii_fields = ['cpf', 'cnpj', 'rg', 'endereco', 'matricula', 'nome', 'email', 'phone']
        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(pii_field in key_lower for pii_field in pii_fields):
                if isinstance(value, str) and value:
                    result[key] = f"[HASHED:{hash_pii_for_cache(value)[:8]}]"
                elif isinstance(value, dict):
                    result[key] = self._hash_pii_in_dict(value)
                else:
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = self._hash_pii_in_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self._hash_pii_in_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    
    async def _extract_with_llm(
        self,
        text: str,
        document_type: str,
        context: Optional[Dict],
        tenant_id: Optional[str]
    ) -> Dict:
        """Extract data using LLM."""
        schema_class = self.SCHEMA_MAP.get(document_type)
        schema_fields = self._get_schema_fields(schema_class)
        
        system_prompt = f"""You are an expert Brazilian legal document parser.
        
Extract structured data from the Portuguese text and return JSON matching this schema:
{json.dumps(schema_fields, indent=2, ensure_ascii=False)}

Extract:
- CPF/CNPJ: Normalize to formatted strings (XXX.XXX.XXX-XX, XX.XXX.XXX/XXXX-XX)
- Dates: ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
- Currency: Convert to decimal numbers (R$ 450.000 -> 450000.00)
- OAB: Format as UF-XXXXXX (e.g., "OAB/SP 123456" -> "SP-123456")
- Matrícula: Extract number and RI from context
- Inferred fields: "à vista" -> condicao: "avista"

Return JSON only, no explanation."""
        
        user_prompt = f"Extract data from:\n\n{text}"
        
        if context:
            user_prompt += f"\n\nContext: {json.dumps(context, ensure_ascii=False)}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            llm_service = get_llm_service()
            from uuid import UUID
            tenant_uuid = None
            if tenant_id:
                try:
                    tenant_uuid = UUID(tenant_id) if isinstance(tenant_id, str) else tenant_id
                except (ValueError, TypeError):
                    tenant_uuid = None
            
            response = await llm_service.chat_completion(
                messages=messages,
                model="gpt-4o-mini",
                temperature=0.1,
                max_tokens=2000,
                tenant_id=tenant_uuid,
            )
            
            parsed = json.loads(response)
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {}
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}", exc_info=True)
            return {}
    
    def _get_schema_fields(self, schema_class) -> Dict:
        """Get schema fields as a dict for LLM prompt."""
        # Create a sample instance to get field structure
        try:
            # Get schema fields from Pydantic model
            fields = {}
            for field_name, field_info in schema_class.__fields__.items():
                fields[field_name] = {
                    "type": str(field_info.type_),
                    "required": field_info.required,
                    "description": field_info.field_info.description if field_info.field_info else None
                }
            return fields
        except:
            return {}
    
    def _normalize_data(self, data: Dict, document_type: str, original_text: str) -> Dict:
        """Normalize extracted data."""
        normalized = {}
        
        for key, value in data.items():
            if value is None:
                continue
            
            # Normalize CPF/CNPJ
            if 'cpf' in key.lower() and isinstance(value, str):
                normalized[key] = self._normalize_cpf(value)
            elif 'cnpj' in key.lower() and isinstance(value, str):
                normalized[key] = self._normalize_cnpj(value)
            # Normalize dates
            elif 'data' in key.lower() or 'date' in key.lower():
                normalized[key] = self._normalize_date(value)
            # Normalize currency
            elif 'preco' in key.lower() or 'valor' in key.lower():
                normalized[key] = self._normalize_currency(value, original_text)
            # Normalize OAB
            elif 'oab' in key.lower():
                normalized[key] = self._normalize_oab(value)
            # Normalize matrícula/RI
            elif 'matricula' in key.lower() or 'ri' in key.lower():
                if isinstance(value, dict):
                    normalized[key] = value
                else:
                    normalized[key] = self._extract_matricula_ri(value, original_text)
            # Recursively normalize nested dicts
            elif isinstance(value, dict):
                normalized[key] = self._normalize_data(value, document_type, original_text)
            # Normalize lists
            elif isinstance(value, list):
                normalized[key] = [
                    self._normalize_data(item, document_type, original_text) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                normalized[key] = value
        
        # Infer additional fields from text
        self._infer_fields(normalized, document_type, original_text)
        
        return normalized
    
    def _normalize_cpf(self, value: str) -> str:
        """Normalize CPF to XXX.XXX.XXX-XX format."""
        digits = re.sub(r'[^\d]', '', str(value))
        if len(digits) == 11:
            return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
        return value
    
    def _normalize_cnpj(self, value: str) -> str:
        """Normalize CNPJ to XX.XXX.XXX/XXXX-XX format."""
        digits = re.sub(r'[^\d]', '', str(value))
        if len(digits) == 14:
            return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
        return value
    
    def _normalize_date(self, value: Any) -> Optional[str]:
        """Normalize date to ISO format."""
        if isinstance(value, str):
            # Try to parse common date formats
            formats = [
                "%d/%m/%Y",
                "%d/%m/%Y %H:%M",
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
            ]
            for fmt in formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.isoformat()
                except:
                    continue
        elif isinstance(value, datetime):
            return value.isoformat()
        return str(value) if value else None
    
    def _normalize_currency(self, value: Any, text: str) -> Optional[float]:
        """Normalize currency to decimal."""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Extract number from string like "R$ 450.000" or "450k"
            text_lower = text.lower()
            
            # Handle "k" suffix (e.g., "450k" -> 450000)
            if 'k' in value.lower() or 'mil' in value.lower():
                number_str = re.sub(r'[^\d.,]', '', value)
                number_str = number_str.replace(',', '.')
                try:
                    num = float(number_str)
                    if 'mil' in text_lower or 'k' in value.lower():
                        num *= 1000
                    return num
                except:
                    pass
            
            # Extract number
            number_str = re.sub(r'[^\d.,]', '', value)
            number_str = number_str.replace('.', '').replace(',', '.')
            try:
                return float(number_str)
            except:
                pass
        
        return None
    
    def _normalize_oab(self, value: str) -> str:
        """Normalize OAB to UF-XXXXXX format."""
        # Remove formatting
        clean = re.sub(r'[^\w]', '', str(value).upper())
        
        # Extract UF and number
        match = re.match(r'^([A-Z]{2})(\d+)$', clean)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        
        # Already formatted?
        if re.match(r'^[A-Z]{2}-\d+$', clean):
            return clean
        
        return value
    
    def _extract_matricula_ri(self, value: Any, text: str) -> Dict:
        """Extract matrícula and RI from text."""
        result = {}
        
        if isinstance(value, dict):
            return value
        
        # Extract matrícula number
        matricula_match = re.search(r'matr[íi]cula\s*:?\s*(\d+)', text, re.IGNORECASE)
        if matricula_match:
            result["matricula"] = matricula_match.group(1)
        
        # Extract RI
        ri_match = re.search(r'(\d+[º°]?\s*RI\s+[^,.\n]+)', text, re.IGNORECASE)
        if ri_match:
            result["ri"] = ri_match.group(1)
        
        return result if result else ({"matricula": str(value)} if value else {})
    
    def _infer_fields(self, data: Dict, document_type: str, text: str):
        """Infer additional fields from text."""
        text_lower = text.lower()
        
        # Infer condicao (payment condition)
        if 'financeiro' in data or document_type in ['escritura_compra_venda', 'registro_compra_venda_ri']:
            if 'à vista' in text_lower or 'a vista' in text_lower or 'avista' in text_lower:
                if 'financeiro' not in data:
                    data['financeiro'] = {}
                data['financeiro']['condicao'] = 'avista'
        
        # Infer poderes for procuracao
        if document_type == 'procuracao_ad_judicia':
            if 'poderes' not in data:
                data['poderes'] = []
            
            if 'gerais forenses' in text_lower or 'gerais' in text_lower:
                data['poderes'].append('gerais_forenses')
            if 'receber citação' in text_lower or 'receber citacao' in text_lower:
                data['poderes'].append('receber_citacao')

