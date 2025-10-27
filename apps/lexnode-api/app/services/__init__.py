"""
Legal document crawlers for LexNode.
"""

from .crawler import CrawlerService
from .database import DatabaseService
from .embeddings import EmbeddingsService
from .indexer import IndexerService
from .normalizer import NormalizerService
from .retrieval import RetrievalService
from .template_matcher import TemplateMatcherService

# Crawler implementations
from .base import BaseCrawler, CrawlResult
from .cnj import CNJCrawler
from .cgj_rj import CGJRJCrawler
