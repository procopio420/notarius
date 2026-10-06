"""
Legal document crawlers for LexNode.
"""

from .crawler import CrawlerService
from .indexer import IndexerService
from .normalizer import NormalizerService
from .retrieval import RetrievalService
from .template_matcher import TemplateMatchingService

# Crawler implementations
from .base import BaseCrawler, CrawlResult
from .cnj import CNJCrawler
from .cgj_rj import CGJRJCrawler
