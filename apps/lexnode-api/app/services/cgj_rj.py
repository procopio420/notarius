"""
CGJ-RJ (Corregedoria Geral de Justiça do Rio de Janeiro) crawler.

Crawls legal documents, resolutions, and norms from the Rio de Janeiro
court system for LexNode RAG service.
"""

import re
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseCrawler, CrawlResult
from packages.observability import get_logger

logger = get_logger(__name__)


class CGJRJCrawler(BaseCrawler):
    """Crawler for CGJ-RJ legal documents."""
    
    def __init__(self):
        super().__init__(
            base_url="https://www.tjrj.jus.br",
            user_agent="NotariusBot/1.0 (+https://notarius.ai/bot)",
            delay_seconds=1.0,
            max_retries=3,
            timeout_seconds=30
        )
        
        # CGJ-RJ specific paths
        self.legal_paths = [
            "/web/guest/corregedoria-geral-de-justica",
            "/web/guest/corregedoria-geral-de-justica/resolucoes",
            "/web/guest/corregedoria-geral-de-justica/normas",
            "/web/guest/corregedoria-geral-de-justica/instrucoes",
            "/web/guest/corregedoria-geral-de-justica/circulares",
        ]
        
        # Patterns for legal document URLs
        self.legal_patterns = [
            r".*resolucao.*",
            r".*norma.*",
            r".*instrucao.*",
            r".*circular.*",
            r".*portaria.*",
            r".*decreto.*",
        ]
    
    async def discover_urls(self) -> List[str]:
        """Discover URLs to crawl from CGJ-RJ."""
        urls = set()
        
        try:
            # Start with main legal paths
            for path in self.legal_paths:
                full_url = urljoin(self.base_url, path)
                page_urls = await self._discover_from_page(full_url)
                urls.update(page_urls)
            
            # Also crawl sitemap if available
            sitemap_urls = await self._discover_from_sitemap()
            urls.update(sitemap_urls)
            
        except Exception as e:
            logger.error(f"Failed to discover URLs from CGJ-RJ: {e}")
        
        return list(urls)
    
    async def _discover_from_page(self, url: str) -> List[str]:
        """Discover URLs from a specific page."""
        urls = set()
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return []
                
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Find all links
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href']
                    full_url = urljoin(url, href)
                    
                    if self.is_valid_url(full_url) and self.should_crawl_url(full_url):
                        urls.add(self.normalize_url(full_url))
                
                # Look for pagination
                pagination_links = soup.find_all('a', href=True, class_=re.compile(r'page|next|previous'))
                for link in pagination_links:
                    href = link['href']
                    full_url = urljoin(url, href)
                    if self.is_valid_url(full_url):
                        # Recursively discover from pagination pages
                        page_urls = await self._discover_from_page(full_url)
                        urls.update(page_urls)
        
        except Exception as e:
            logger.warning(f"Failed to discover URLs from page {url}: {e}")
        
        return list(urls)
    
    async def _discover_from_sitemap(self) -> List[str]:
        """Discover URLs from sitemap."""
        urls = set()
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/robots.txt",
        ]
        
        for sitemap_url in sitemap_urls:
            try:
                async with self.session.get(sitemap_url) as response:
                    if response.status != 200:
                        continue
                    
                    content = await response.text()
                    
                    if sitemap_url.endswith('.xml'):
                        # Parse XML sitemap
                        urls.update(self._parse_xml_sitemap(content))
                    else:
                        # Parse robots.txt for sitemap references
                        urls.update(self._parse_robots_txt(content))
            
            except Exception as e:
                logger.warning(f"Failed to parse sitemap {sitemap_url}: {e}")
        
        return list(urls)
    
    def _parse_xml_sitemap(self, content: str) -> List[str]:
        """Parse XML sitemap content."""
        urls = set()
        
        try:
            soup = BeautifulSoup(content, 'xml')
            locs = soup.find_all('loc')
            
            for loc in locs:
                url = loc.get_text().strip()
                if self.is_valid_url(url) and self.should_crawl_url(url):
                    urls.add(self.normalize_url(url))
        
        except Exception as e:
            logger.warning(f"Failed to parse XML sitemap: {e}")
        
        return list(urls)
    
    def _parse_robots_txt(self, content: str) -> List[str]:
        """Parse robots.txt for sitemap references."""
        urls = set()
        
        try:
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line.lower().startswith('sitemap:'):
                    sitemap_url = line.split(':', 1)[1].strip()
                    if self.is_valid_url(sitemap_url):
                        # Recursively parse sitemap
                        urls.update(self._discover_from_sitemap())
        
        except Exception as e:
            logger.warning(f"Failed to parse robots.txt: {e}")
        
        return list(urls)
    
    def should_crawl_url(self, url: str) -> bool:
        """Determine if URL should be crawled."""
        if not self.is_valid_url(url):
            return False
        
        # Check if URL matches legal document patterns
        url_lower = url.lower()
        for pattern in self.legal_patterns:
            if re.search(pattern, url_lower):
                return True
        
        # Check for specific CGJ-RJ legal paths
        legal_keywords = [
            'corregedoria',
            'resolucao',
            'norma',
            'instrucao',
            'circular',
            'portaria',
            'decreto',
            'ato',
            'regulamento',
        ]
        
        return any(keyword in url_lower for keyword in legal_keywords)
    
    def extract_legal_content(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract legal content from parsed HTML."""
        try:
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find main content area
            content_selectors = [
                'main',
                '.content',
                '.main-content',
                '.document-content',
                '.legal-content',
                '#content',
                '.article-content',
                '.post-content',
            ]
            
            content_element = None
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
            
            if not content_element:
                # Fallback to body
                content_element = soup.find('body')
            
            if not content_element:
                return None
            
            # Extract text content
            text = content_element.get_text()
            
            # Clean up text
            lines = text.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if line and len(line) > 10:  # Filter out very short lines
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
        
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {e}")
            return None
    
    def extract_metadata(self, soup: BeautifulSoup, url: str) -> dict:
        """Extract CGJ-RJ specific metadata."""
        metadata = super().extract_metadata(soup, url)
        
        # Add CGJ-RJ specific metadata
        metadata.update({
            "source": "CGJ-RJ",
            "jurisdiction": "RJ",
            "crawler": "cgj_rj",
        })
        
        # Try to extract document type from URL or content
        url_lower = url.lower()
        if 'resolucao' in url_lower:
            metadata["doc_type"] = "resolucao"
        elif 'norma' in url_lower:
            metadata["doc_type"] = "norma"
        elif 'instrucao' in url_lower:
            metadata["doc_type"] = "instrucao"
        elif 'circular' in url_lower:
            metadata["doc_type"] = "circular"
        elif 'portaria' in url_lower:
            metadata["doc_type"] = "portaria"
        elif 'decreto' in url_lower:
            metadata["doc_type"] = "decreto"
        
        # Try to extract document number
        doc_number_match = re.search(r'(\d+)[/\-](\d+)', url)
        if doc_number_match:
            metadata["document_number"] = doc_number_match.group(0)
        
        # Try to extract date from content
        date_patterns = [
            r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})',
            r'(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})',
        ]
        
        text_content = soup.get_text()
        for pattern in date_patterns:
            date_match = re.search(pattern, text_content)
            if date_match:
                metadata["extracted_date"] = date_match.group(0)
                break
        
        return metadata
