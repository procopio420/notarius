"""
Base crawler class for legal document crawling.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from packages.observability import get_logger

logger = get_logger(__name__)


class CrawlResult:
    """Result of a crawl operation."""
    
    def __init__(
        self,
        url: str,
        content: str,
        title: str,
        status_code: int,
        content_type: str,
        processing_time_ms: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.url = url
        self.content = content
        self.title = title
        self.status_code = status_code
        self.content_type = content_type
        self.processing_time_ms = processing_time_ms
        self.metadata = metadata or {}


class BaseCrawler(ABC):
    """Abstract base class for legal document crawlers."""
    
    def __init__(
        self,
        base_url: str,
        user_agent: str = "NotariusBot/1.0 (+https://notarius.ai/bot)",
        delay_seconds: float = 1.0,
        max_retries: int = 3,
        timeout_seconds: int = 30
    ):
        self.base_url = base_url
        self.user_agent = user_agent
        self.delay_seconds = delay_seconds
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout_seconds),
            headers={"User-Agent": self.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def crawl_url(self, url: str) -> Optional[CrawlResult]:
        """Crawl a single URL with retry logic."""
        for attempt in range(self.max_retries):
            try:
                start_time = time.time()
                
                async with self.session.get(url) as response:
                    content = await response.text()
                    processing_time = int((time.time() - start_time) * 1000)
                    
                    # Parse content
                    soup = BeautifulSoup(content, 'html.parser')
                    title = soup.find('title')
                    title_text = title.get_text().strip() if title else url
                    
                    # Extract metadata
                    metadata = self.extract_metadata(soup, url)
                    
                    return CrawlResult(
                        url=url,
                        content=content,
                        title=title_text,
                        status_code=response.status,
                        content_type=response.headers.get('content-type', ''),
                        processing_time_ms=processing_time,
                        metadata=metadata
                    )
                    
            except Exception as e:
                logger.warning(
                    f"Crawl attempt {attempt + 1} failed for {url}",
                    error=str(e),
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All crawl attempts failed for {url}", error=str(e))
                    return None
    
    def extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from parsed HTML."""
        metadata = {
            "url": url,
            "domain": urlparse(url).netloc,
        }
        
        # Extract meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[f"meta_{name}"] = content
        
        # Extract headings
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        metadata["headings"] = [h.get_text().strip() for h in headings]
        
        return metadata
    
    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid for crawling."""
        parsed = urlparse(url)
        
        # Must be HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Must be from the same domain
        if parsed.netloc != urlparse(self.base_url).netloc:
            return False
        
        # Skip certain file types
        skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        return True
    
    def normalize_url(self, url: str) -> str:
        """Normalize URL for consistent storage."""
        # Remove fragment
        if '#' in url:
            url = url.split('#')[0]
        
        # Remove query parameters (optional, depending on use case)
        # if '?' in url:
        #     url = url.split('?')[0]
        
        return url
    
    @abstractmethod
    async def discover_urls(self) -> List[str]:
        """Discover URLs to crawl."""
        pass
    
    @abstractmethod
    def should_crawl_url(self, url: str) -> bool:
        """Determine if URL should be crawled."""
        pass
    
    @abstractmethod
    def extract_legal_content(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract legal content from parsed HTML."""
        pass
    
    async def crawl_all(self) -> List[CrawlResult]:
        """Crawl all discovered URLs."""
        results = []
        urls = await self.discover_urls()
        
        logger.info(f"Starting crawl of {len(urls)} URLs from {self.base_url}")
        
        for i, url in enumerate(urls):
            if not self.should_crawl_url(url):
                continue
            
            result = await self.crawl_url(url)
            if result:
                results.append(result)
            
            # Rate limiting
            if i < len(urls) - 1:  # Don't delay after the last URL
                await asyncio.sleep(self.delay_seconds)
        
        logger.info(f"Crawl completed: {len(results)} successful, {len(urls) - len(results)} failed")
        return results
