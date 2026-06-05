"""新闻处理"""

from .dedup import deduplicate_news
from .classify import classify_sentiment, classify_importance
from .sentiment import analyze_sentiment
from .entity import extract_entities

__all__ = [
    "deduplicate_news",
    "classify_sentiment",
    "classify_importance",
    "analyze_sentiment",
    "extract_entities",
]
