"""
Normalizer for legal rules with metadata extraction.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List, Optional

from ..embeddings import generate_embedding

logger = logging.getLogger(__name__)


class LegalRuleNormalizer:
    """Normalizes legal documents into LegalRule format with metadata."""
    
    def __init__(self):
        pass
    
    async def normalize_to_rule(
        self,
        document: Dict,
        document_types: Optional[List[str]] = None,
        checklist_items: Optional[List[str]] = None
    ) -> Dict:
        """
        Normalize a legal document into a LegalRule format.
        
        Args:
            document: Legal document dict
            document_types: List of applicable document types
            checklist_items: List of checklist items
            
        Returns:
            Normalized rule dict ready for LegalRule model
        """
        logger.info(f"Normalizing document to rule: {document.get('id')}")
        
        # Extract metadata
        fonte = self._extract_fonte(document)
        artigo = self._extract_artigo(document)
        provimento = self._extract_provimento(document)
        data = self._extract_data(document)
        uf = document.get("jurisdiction") or document.get("metadata", {}).get("uf")
        
        # Generate citation
        citation = self._generate_citation(fonte, artigo, provimento)
        
        # Determine precedence
        precedence = self._determine_precedence(fonte, uf)
        
        # Generate embedding
        content_for_embedding = self._prepare_content_for_embedding(document)
        embedding = await generate_embedding(content_for_embedding)
        
        return {
            "fonte": fonte,
            "artigo": artigo,
            "provimento": provimento,
            "data": data,
            "uf": uf,
            "document_types": document_types or self._infer_document_types(document),
            "checklist_items": checklist_items or [],
            "citation": citation,
            "precedence": precedence,
            "content": document.get("content", ""),
            "embedding": embedding,
            "metadata_json": {
                **document.get("metadata", {}),
                "source_url": document.get("url"),
                "normalized_at": datetime.utcnow().isoformat(),
            }
        }
    
    def _extract_fonte(self, document: Dict) -> str:
        """Extract fonte from document."""
        source = document.get("source", "")
        if "CNJ" in source:
            return f"CNJ {document.get('metadata', {}).get('numero', '')}"
        elif "CGJ" in source:
            uf = document.get("jurisdiction", "")
            return f"CGJ/{uf}"
        elif "Código Civil" in source or "CC" in source:
            return "CC/2002"
        elif "Lei 6.015" in source:
            return "Lei 6.015/73"
        elif "Lei 8.935" in source:
            return "Lei 8.935/94"
        return source
    
    def _extract_artigo(self, document: Dict) -> Optional[str]:
        """Extract artigo reference from document."""
        metadata = document.get("metadata", {})
        if "artigo" in metadata:
            return metadata["artigo"]
        
        # Try to extract from content
        content = document.get("content", "")
        match = re.search(r'Art\.\s+(\d+[^\n]*)', content, re.IGNORECASE)
        if match:
            return f"Art. {match.group(1)}"
        
        return None
    
    def _extract_provimento(self, document: Dict) -> Optional[str]:
        """Extract provimento reference."""
        metadata = document.get("metadata", {})
        if "numero" in metadata and "provimento" in document.get("type", ""):
            return f"Provimento {metadata['numero']}"
        return None
    
    def _extract_data(self, document: Dict) -> Optional[datetime]:
        """Extract effective date from document."""
        metadata = document.get("metadata", {})
        date_str = metadata.get("data_publicacao") or metadata.get("data")
        
        if date_str:
            try:
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except:
                pass
        
        return None
    
    def _generate_citation(self, fonte: str, artigo: Optional[str], provimento: Optional[str]) -> str:
        """Generate citation string."""
        parts = [fonte]
        if artigo:
            parts.append(artigo)
        if provimento:
            parts.append(provimento)
        return ", ".join(parts)
    
    def _determine_precedence(self, fonte: str, uf: Optional[str]) -> str:
        """Determine rule precedence."""
        if "CNJ" in fonte or "Lei" in fonte or "CC" in fonte:
            return "federal"
        elif "CGJ" in fonte and uf:
            return "state"
        else:
            return "internal"
    
    def _infer_document_types(self, document: Dict) -> List[str]:
        """Infer applicable document types from content."""
        content = (document.get("content", "") + " " + document.get("title", "")).lower()
        doc_types = []
        
        if "procuração" in content or "procuracao" in content:
            if "veículo" in content or "veiculo" in content:
                doc_types.append("procuracao_veiculo")
            elif "judicial" in content or "ad judicia" in content:
                doc_types.append("procuracao_ad_judicia")
            else:
                doc_types.append("procuracao")
        
        if "compra e venda" in content or "compra/venda" in content:
            if "imóvel" in content or "imovel" in content:
                doc_types.append("escritura_compra_venda")
                doc_types.append("registro_compra_venda_ri")
        
        if "nascimento" in content:
            doc_types.append("assento_nascimento")
        
        if "divórcio" in content or "divorcio" in content:
            doc_types.append("averbacao_divorcio")
        
        if "construção" in content or "construcao" in content:
            doc_types.append("averbacao_construcao")
        
        if "locação" in content or "locacao" in content:
            doc_types.append("registro_contrato_locacao")
        
        if "protesto" in content:
            doc_types.append("protesto_titulo")
        
        if "certidão" in content or "certidao" in content:
            doc_types.append("certidao_onus_reais")
        
        return doc_types if doc_types else ["geral"]
    
    def _prepare_content_for_embedding(self, document: Dict) -> str:
        """Prepare content for embedding generation."""
        parts = []
        
        if document.get("title"):
            parts.append(document["title"])
        
        if document.get("content"):
            # Use first 500 chars for embedding
            parts.append(document["content"][:500])
        
        return " ".join(parts)
    
    async def normalize_batch(
        self,
        documents: List[Dict],
        document_types_map: Optional[Dict[str, List[str]]] = None,
        checklist_map: Optional[Dict[str, List[str]]] = None
    ) -> List[Dict]:
        """Normalize a batch of documents to rules."""
        normalized = []
        
        for doc in documents:
            doc_id = doc.get("id", "")
            doc_types = (document_types_map or {}).get(doc_id)
            checklist = (checklist_map or {}).get(doc_id)
            
            rule = await self.normalize_to_rule(doc, doc_types, checklist)
            normalized.append(rule)
        
        return normalized

