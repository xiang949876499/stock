"""新闻采集"""

from .base import NewsCollector
from .eastmoney import EastMoneyCollector

__all__ = [
    "NewsCollector",
    "EastMoneyCollector",
]
