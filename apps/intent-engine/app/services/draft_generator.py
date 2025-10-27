"""
Draft generation service using AI.
"""

import os
import json
import logging
from typing import Dict, List, Optional
import httpx

from .llm import get_llm_service

logger = logging.getLogger(__name__)


class DraftGenerator:
    """Generate legal document drafts from structured intents."""
    
    def __init__(self):
        self.lexnode_url = os.getenv("LEXNODE_URL", "http://lexnode-api:8000")
    
    async def generate_draft(
        self,
        parsed_intent: Dict,
        template_content: Optional[str] = None,
        legal_citations: Optional[List[Dict]] = None,
    ) -> Dict:
        """
        Generate document draft from parsed intent.
        
        Args:
            parsed_intent: Structured intent from parser
            template_content: Optional template to follow
            legal_citations: Optional legal citations to ground the document
            
        Returns:
            Draft with content, placeholders, citations, confidence
        """
        logger.info(f"Generating draft for {parsed_intent.get('document_type')}")
        
        # Get legal citations if not provided
        if legal_citations is None:
            legal_citations = await self._get_legal_citations(parsed_intent)
        
        # Build prompt for draft generation
        system_prompt = self._build_draft_system_prompt(parsed_intent.get('document_type'))
        user_prompt = self._build_draft_user_prompt(
            parsed_intent,
            template_content,
            legal_citations
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        try:
            # Generate draft content
            llm_service = get_llm_service()
            draft_content = await llm_service.chat_completion(
                messages=messages,
                model="gpt-4o-mini",
                temperature=0.5,  # Medium creativity
                max_tokens=3000,
            )
            
            # Replace PII with placeholders
            draft_with_placeholders = self._replace_pii_with_placeholders(
                draft_content,
                parsed_intent.get("entities", {})
            )
            
            # Calculate grounding confidence
            grounding_confidence = self._calculate_grounding_confidence(legal_citations)
            
            return {
                "content": draft_with_placeholders,
                "original_content": draft_content,
                "placeholders": self._extract_placeholders(draft_with_placeholders),
                "citations": legal_citations or [],
                "grounding_confidence": grounding_confidence,
                "document_type": parsed_intent.get("document_type"),
                "metadata": {
                    "intent_confidence": parsed_intent.get("confidence", 0.0),
                    "entities_count": len(parsed_intent.get("entities", {})),
                    "citations_count": len(legal_citations) if legal_citations else 0,
                }
            }
            
        except Exception as e:
            logger.error(f"Draft generation failed: {e}", exc_info=True)
            raise
    
    def _build_draft_system_prompt(self, document_type: str) -> str:
        """Build system prompt for draft generation."""
        document_descriptions = {
            "procuracao": "procuração (power of attorney)",
            "certidao": "certidão (certificate)",
            "testamento": "testamento (will)",
            "escritura": "escritura (deed)",
            "contrato": "contrato (contract)",
        }
        
        doc_desc = document_descriptions.get(document_type, document_type)
        
        return f"""You are an expert Brazilian notary assistant specializing in {doc_desc}.

Generate a professional, legally sound document in Portuguese following Brazilian legal standards.

Important:
1. Use formal legal language (linguagem jurídica formal)
2. Include proper legal structure and clauses
3. Reference provided legal citations where appropriate
4. Use {{{{PLACEHOLDER_NAME}}}} for PII values that need to be filled in
5. Follow Brazilian notary document formatting
6. Include proper legal disclaimers and formalities
7. Be concise but complete

Output the document text directly, no JSON wrapping."""
    
    def _build_draft_user_prompt(
        self,
        parsed_intent: Dict,
        template_content: Optional[str],
        legal_citations: Optional[List[Dict]]
    ) -> str:
        """Build user prompt for draft generation."""
        prompt = f"""Generate a {parsed_intent.get('document_type')} with these details:

Action: {parsed_intent.get('action')}
Entities: {json.dumps(parsed_intent.get('entities', {}), ensure_ascii=False, indent=2)}
"""
        
        if template_content:
            prompt += f"\n\nFollow this template structure:\n{template_content[:500]}"
        
        if legal_citations:
            prompt += f"\n\nGround the document using these legal citations:\n"
            for citation in legal_citations[:3]:  # Top 3 citations
                prompt += f"- {citation.get('source')}: {citation.get('excerpt', '')[:200]}\n"
        
        prompt += "\n\nGenerate the complete document now."
        
        return prompt
    
    async def _get_legal_citations(self, parsed_intent: Dict) -> List[Dict]:
        """Get legal citations from LexNode."""
        try:
            from packages.core.http_client import get_http_client
            http_client = get_http_client()
            response = await http_client.post(
                f"{self.lexnode_url}/api/v1/lexnode/retrieve",
                json={
                    "query": f"{parsed_intent.get('document_type')} {parsed_intent.get('action')}",
                    "jurisdiction": "RJ",
                    "limit": 5,
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("results", [])
            else:
                logger.warning(f"LexNode returned {response.status_code}")
                return []
                    
        except Exception as e:
            logger.warning(f"Failed to get legal citations: {e}")
            return []
    
    def _replace_pii_with_placeholders(self, content: str, entities: Dict) -> str:
        """Replace PII values with placeholders."""
        # This is a simple replacement - in production would use more sophisticated NER
        for key, value in entities.items():
            if value and isinstance(value, str):
                placeholder = f"{{{{{key.upper()}}}}}"
                content = content.replace(value, placeholder)
        
        return content
    
    def _extract_placeholders(self, content: str) -> List[str]:
        """Extract all placeholders from content."""
        import re
        placeholders = re.findall(r'\{\{([A-Z_]+)\}\}', content)
        return list(set(placeholders))
    
    def _calculate_grounding_confidence(self, citations: Optional[List[Dict]]) -> float:
        """Calculate confidence based on legal grounding."""
        if not citations:
            return 0.5  # No citations = medium confidence
        
        # Average relevance scores
        relevance_scores = [c.get("relevance", 0.5) for c in citations]
        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0.5
        
        # Boost confidence if we have multiple good citations
        citation_bonus = min(len(citations) * 0.1, 0.3)
        
        return min(avg_relevance + citation_bonus, 1.0)

