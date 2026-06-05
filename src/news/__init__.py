"""新闻层"""

from .collectors.base import NewsCollector
from .collectors.eastmoney import EastMoneyCollector
from .processors.dedup import deduplicate_news
from .processors.classify import classify_sentiment, classify_importance
from .processors.sentiment import analyze_sentiment
from .processors.entity import extract_entities
from .analysis.analyzer import NewsAnalyzer
from .service import NewsService

__all__ = [
    "NewsCollector",
    "EastMoneyCollector",
    "deduplicate_news",
    "classify_sentiment",
    "classify_importance",
    "analyze_sentiment",
    "extract_entities",
    "NewsAnalyzer",
    "NewsService",
]
