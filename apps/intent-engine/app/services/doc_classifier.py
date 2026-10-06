"""
Document classifier service for multi-label classification.
Maps free-text to {tipo_documento, especialidade, confianca}.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple

from .llm import get_llm_service

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Multi-label classifier for Brazilian notarial documents."""
    
    # Document type to specialty mapping
    DOCUMENT_TYPE_MAP = {
        "escritura_compra_venda": "tabelionato_notas",
        "procuracao_ad_judicia": "tabelionato_notas",
        "procuracao_veiculo": "tabelionato_notas",
        "ata_notarial_constatacao": "tabelionato_notas",
        "assento_nascimento": "rcpn",
        "averbacao_divorcio": "rcpn",
        "registro_compra_venda_ri": "registro_imoveis",
        "averbacao_construcao": "registro_imoveis",
        "registro_contrato_locacao": "rtd",
        "notificacao_extrajudicial": "rtd",
        "protesto_titulo": "protesto",
        "certidao_onus_reais": "registro_imoveis",
    }
    
    # Keywords for document type detection
    KEYWORD_PATTERNS = {
        "escritura_compra_venda": [
            "escritura", "compra e venda", "compra/venda", "vendedor", "comprador",
            "imóvel", "imovel", "matrícula", "matricula", "preço", "preco"
        ],
        "procuracao_ad_judicia": [
            "procuração", "procuracao", "ad judicia", "judicial", "outorgante",
            "outorgado", "oab", "poderes forenses"
        ],
        "procuracao_veiculo": [
            "procuração", "procuracao", "veículo", "veiculo", "automóvel", "automovel",
            "placa", "crlv", "crv", "proprietário", "proprietario"
        ],
        "ata_notarial_constatacao": [
            "ata notarial", "constatação", "constatacao", "instagram", "facebook",
            "conteúdo web", "conteudo web", "urls", "prints"
        ],
        "assento_nascimento": [
            "nascimento", "registro de nascimento", "recém-nascido", "recem-nascido",
            "genitores", "mãe", "mae", "pai", "dnv"
        ],
        "averbacao_divorcio": [
            "divórcio", "divorcio", "averb", "averbacao", "casamento", "sentença",
            "sentenca", "transitado em julgado", "renomeação", "renomeacao"
        ],
        "registro_compra_venda_ri": [
            "registro de imóvel", "registro de imovel", "ri", "registro imobiliário",
            "registro imobiliario", "matrícula", "matricula", "título", "titulo"
        ],
        "averbacao_construcao": [
            "averb", "averbacao", "construção", "construcao", "obra", "habite-se",
            "habite se", "art-rrt", "área", "area", "m²", "m2"
        ],
        "registro_contrato_locacao": [
            "locação", "locacao", "aluguel", "contrato de locação", "contrato de locacao",
            "locador", "locatário", "locatario", "caução", "caucao"
        ],
        "notificacao_extrajudicial": [
            "notificação", "notificacao", "extrajudicial", "inadimplemento", "mora",
            "purgar", "prazo"
        ],
        "protesto_titulo": [
            "protesto", "duplicata", "nota promissória", "nota promissoria", "título",
            "titulo", "vencimento", "devedor", "praça", "praca"
        ],
        "certidao_onus_reais": [
            "certidão", "certidao", "ônus reais", "onus reais", "matrícula", "matricula"
        ],
    }
    
    def __init__(self):
        self.llm_service = None
    
    async def classify(
        self,
        text: str,
        context: Optional[Dict] = None,
        tenant_id: Optional[str] = None
    ) -> Dict:
        """
        Classify free-text input into document type and specialty.
        
        Args:
            text: Free-text input in Portuguese
            context: Additional context (optional)
            tenant_id: Tenant ID for LLM calls
            
        Returns:
            Dict with tipo_documento, especialidade, confianca
        """
        logger.info(f"Classifying document from text: {text[:100]}...")
        
        # First, try keyword-based matching (fast)
        keyword_result = self._classify_by_keywords(text)
        
        # Then, use LLM for more nuanced classification
        llm_result = await self._classify_with_llm(text, context, tenant_id)
        
        # Combine results: use LLM if confidence is high, otherwise use keywords
        if llm_result.get("confianca", 0) > 0.7:
            result = llm_result
        elif keyword_result.get("confianca", 0) > 0.5:
            result = keyword_result
        else:
            # Fallback: use LLM result even if low confidence
            result = llm_result
        
        # Ensure specialty is set
        if result.get("tipo_documento"):
            result["especialidade"] = self.DOCUMENT_TYPE_MAP.get(
                result["tipo_documento"],
                "tabelionato_notas"  # Default
            )
        
        logger.info(
            f"Classification result: tipo={result.get('tipo_documento')}, "
            f"especialidade={result.get('especialidade')}, "
            f"confianca={result.get('confianca')}"
        )
        
        return result
    
    def _classify_by_keywords(self, text: str) -> Dict:
        """Fast keyword-based classification."""
        text_lower = text.lower()
        
        scores = {}
        for doc_type, keywords in self.KEYWORD_PATTERNS.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                # Score based on number of keyword matches
                scores[doc_type] = min(matches / len(keywords), 0.8)  # Cap at 0.8 for keyword matching
        
        if scores:
            best_type = max(scores.items(), key=lambda x: x[1])
            return {
                "tipo_documento": best_type[0],
                "confianca": best_type[1],
                "method": "keyword"
            }
        
        return {
            "tipo_documento": None,
            "confianca": 0.3,
            "method": "keyword"
        }
    
    async def _classify_with_llm(
        self,
        text: str,
        context: Optional[Dict],
        tenant_id: Optional[str]
    ) -> Dict:
        """LLM-based classification with hard negatives support."""
        system_prompt = """You are an expert Brazilian legal document classifier.
        
Your task is to classify free-text requests into specific document types used in Brazilian notarial and registry services.

Supported document types:
- escritura_compra_venda (tabelionato_notas)
- procuracao_ad_judicia (tabelionato_notas)
- procuracao_veiculo (tabelionato_notas)
- ata_notarial_constatacao (tabelionato_notas)
- assento_nascimento (rcpn)
- averbacao_divorcio (rcpn)
- registro_compra_venda_ri (registro_imoveis)
- averbacao_construcao (registro_imoveis)
- registro_contrato_locacao (rtd)
- notificacao_extrajudicial (rtd)
- protesto_titulo (protesto)
- certidao_onus_reais (registro_imoveis)

The input may contain:
- Abreviações (e.g., "escr comp e venda", "proc", "RI")
- Typos and misspellings
- Numbers without masks (e.g., CPF without dots/dashes)
- Informal language

Output JSON only (no explanation):
{
    "tipo_documento": "escritura_compra_venda",
    "confianca": 0.95,
    "indicadores": ["vendedor", "comprador", "imóvel", "matrícula"]
}"""
        
        user_prompt = f"Classify this request:\n\n{text}"
        
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
                temperature=0.2,  # Low temperature for consistency
                max_tokens=200,
                tenant_id=tenant_uuid,
            )
            
            parsed = json.loads(response)
            parsed["method"] = "llm"
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return {
                "tipo_documento": None,
                "confianca": 0.3,
                "method": "llm_fallback"
            }
        except Exception as e:
            logger.error(f"LLM classification failed: {e}", exc_info=True)
            return {
                "tipo_documento": None,
                "confianca": 0.2,
                "method": "llm_error"
            }

