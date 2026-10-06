"""
Crawler for state CGJ (Corregedoria Geral de Justiça) normas by UF.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional

from packages.core.http_client import get_http_client

logger = logging.getLogger(__name__)


class CGJCrawler:
    """Crawler for state CGJ normas by UF."""
    
    # Base URLs for CGJ by state (examples)
    CGJ_URLS = {
        "SP": "https://www.tjsp.jus.br",
        "RJ": "https://www.tjrj.jus.br",
        "PR": "https://www.tjpr.jus.br",
        "RS": "https://www.tjrs.jus.br",
        "MG": "https://www.tjmg.jus.br",
    }
    
    def __init__(self):
        self.http_client = None
    
    async def initialize(self):
        """Initialize HTTP client."""
        from packages.core.http_client import get_http_client
        self.http_client = get_http_client()
    
    async def crawl_cgj_normas(
        self,
        uf: str,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Crawl CGJ normas for a specific state.
        
        Args:
            uf: State abbreviation (SP, RJ, etc.)
            limit: Maximum number of normas to crawl
            
        Returns:
            List of normalized CGJ norma documents
        """
        logger.info(f"Starting CGJ normas crawl for {uf}")
        
        if not self.http_client:
            await self.initialize()
        
        normas = []
        
        # In production, this would crawl actual CGJ pages
        # For now, we'll create sample norma structures
        
        sample_normas = [
            {
                "id": f"cgj-{uf.lower()}-norma-001",
                "title": f"Norma CGJ/{uf} 123/2024 - Procedimentos de Registro",
                "content": f"Art. 1º As normas de registro de imóveis no estado de {uf}...",
                "url": f"{self.CGJ_URLS.get(uf, '')}/normas/123-2024",
                "source": f"CGJ/{uf}",
                "jurisdiction": uf,
                "metadata": {
                    "numero": "123/2024",
                    "data_publicacao": "2024-01-15",
                    "tipo": "norma_cgj",
                    "uf": uf
                }
            }
        ]
        
        for norma in sample_normas[:limit] if limit else sample_normas:
            normalized = await self._normalize_norma(norma)
            normas.append(normalized)
        
        logger.info(f"Crawled {len(normas)} CGJ normas for {uf}")
        return normas
    
    async def _normalize_norma(self, norma: Dict) -> Dict:
        """Normalize a CGJ norma document."""
        return {
            "id": norma["id"],
            "title": norma["title"],
            "content": norma["content"],
            "source": norma["source"],
            "url": norma["url"],
            "jurisdiction": norma["jurisdiction"],
            "type": "norma_cgj",
            "metadata": {
                **norma.get("metadata", {}),
                "crawled_at": datetime.utcnow().isoformat(),
            }
        }

