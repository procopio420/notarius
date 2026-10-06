"""
Legal knowledge ingestion pipelines.
"""

from .cnj_crawler import CNJCrawler
from .cgj_crawler import CGJCrawler
from .legal_codes_crawler import LegalCodesCrawler
from .fee_tables_crawler import FeeTablesCrawler
from .normalizer import LegalRuleNormalizer

__all__ = [
    "CNJCrawler",
    "CGJCrawler",
    "LegalCodesCrawler",
    "FeeTablesCrawler",
    "LegalRuleNormalizer",
]

