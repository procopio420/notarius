"""
Crawler for CNJ (Conselho Nacional de Justiça) Provimentos.
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

from packages.core.http_client import get_http_client

logger = logging.getLogger(__name__)


class CNJCrawler:
    """Crawler for CNJ Provimentos and normative texts."""
    
    def __init__(self):
        self.base_url = "https://www.cnj.jus.br"
        self.http_client = None
    
    async def initialize(self):
        """Initialize HTTP client."""
        from packages.core.http_client import get_http_client
        self.http_client = get_http_client()
    
    async def crawl_provimentos(
        self,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Crawl CNJ Provimentos.
        
        Args:
            limit: Maximum number of provimentos to crawl
            
        Returns:
            List of normalized provimento documents
        """
        logger.info("Starting CNJ Provimentos crawl")
        
        if not self.http_client:
            await self.initialize()
        
        provimentos = []
        
        # In production, this would crawl actual CNJ pages
        # For now, we'll create sample provimento structures
        
        sample_provimentos = [
            {
                "id": "cnj-provimento-001",
                "title": "Provimento CNJ 123/2024 - Normas para Registros Públicos",
                "content": "Art. 1º As normas de registro de imóveis devem seguir...",
                "url": "https://www.cnj.jus.br/provimentos/123-2024",
                "source": "CNJ",
                "jurisdiction": "BR",
                "metadata": {
                    "numero": "123/2024",
                    "data_publicacao": "2024-01-15",
                    "tipo": "provimento"
                }
            }
        ]
        
        for prov in sample_provimentos[:limit] if limit else sample_provimentos:
            normalized = await self._normalize_provimento(prov)
            provimentos.append(normalized)
        
        logger.info(f"Crawled {len(provimentos)} CNJ Provimentos")
        return provimentos
    
    async def _normalize_provimento(self, prov: Dict) -> Dict:
        """Normalize a provimento document."""
        # Extract articles
        articles = self._extract_articles(prov.get("content", ""))
        
        return {
            "id": prov["id"],
            "title": prov["title"],
            "content": prov["content"],
            "source": prov["source"],
            "url": prov["url"],
            "jurisdiction": prov["jurisdiction"],
            "type": "provimento",
            "metadata": {
                **prov.get("metadata", {}),
                "articles": articles,
                "crawled_at": datetime.utcnow().isoformat(),
            }
        }
    
    def _extract_articles(self, content: str) -> List[Dict]:
        """Extract articles from provimento text."""
        articles = []
        pattern = r'(?:Art\.|Artigo)\s+(\d+)[^\n]*([^\n]+(?:\n(?!Art\.|Artigo)[^\n]+)*)'
        
        matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
        
        for match in matches:
            articles.append({
                "number": match.group(1),
                "text": match.group(2).strip(),
            })
        
        return articles

