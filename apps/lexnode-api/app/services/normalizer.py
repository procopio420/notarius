"""
Document normalization service.
"""

import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class NormalizerService:
    """Normalizes crawled legal documents."""
    
    def normalize_document(self, document: Dict) -> Dict:
        """
        Normalize a legal document.
        
        Args:
            document: Raw crawled document
            
        Returns:
            Normalized document
        """
        logger.info(f"Normalizing document: {document.get('id')}")
        
        # Clean content
        cleaned_content = self._clean_text(document.get("content", ""))
        
        # Extract structure
        structure = self._extract_structure(cleaned_content)
        
        # Extract articles
        articles = self._extract_articles(cleaned_content)
        
        # Generate summary
        summary = self._generate_summary(cleaned_content, articles)
        
        return {
            "id": document.get("id"),
            "title": document.get("title"),
            "content": cleaned_content,
            "summary": summary,
            "structure": structure,
            "articles": articles,
            "metadata": {
                **document.get("metadata", {}),
                "original_length": len(document.get("content", "")),
                "cleaned_length": len(cleaned_content),
                "article_count": len(articles),
            },
            "source": document.get("source"),
            "url": document.get("url"),
            "type": document.get("type"),
            "jurisdiction": document.get("jurisdiction"),
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep Portuguese accents
        # text = re.sub(r'[^\w\s\-.,;:()\[\]áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]', '', text)
        
        # Normalize line breaks
        text = text.replace('\r\n', '\n')
        
        # Trim
        text = text.strip()
        
        return text
    
    def _extract_structure(self, content: str) -> Dict:
        """Extract document structure."""
        structure = {
            "has_articles": "Art." in content or "Artigo" in content,
            "has_paragraphs": "§" in content or "Parágrafo" in content,
            "has_chapters": "Capítulo" in content or "CAPÍTULO" in content,
            "has_sections": "Seção" in content or "SEÇÃO" in content,
        }
        
        return structure
    
    def _extract_articles(self, content: str) -> List[Dict]:
        """Extract articles from legal text."""
        articles = []
        
        # Pattern for articles: Art. 123 or Artigo 123
        pattern = r'(?:Art\.|Artigo)\s+(\d+)[^\n]*([^\n]+(?:\n(?!Art\.|Artigo)[^\n]+)*)'
        
        matches = re.finditer(pattern, content, re.MULTILINE)
        
        for match in matches:
            article_num = match.group(1)
            article_text = match.group(2).strip()
            
            articles.append({
                "number": article_num,
                "text": article_text[:500],  # Limit length
            })
        
        return articles
    
    def _generate_summary(self, content: str, articles: List[Dict]) -> str:
        """Generate document summary."""
        # Simple summary: first 200 chars + article count
        summary = content[:200]
        
        if articles:
            summary += f"\n\nContém {len(articles)} artigos."
        
        return summary

