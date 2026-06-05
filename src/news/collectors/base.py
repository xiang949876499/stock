"""新闻采集基类"""

from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

from src.data.models import Market, NewsItem


class NewsCollector(ABC):
    """新闻采集基类"""

    @abstractmethod
    async def collect(
        self,
        symbol: str,
        market: Market,
        limit: int = 50
    ) -> list[NewsItem]:
        """采集新闻"""
        pass
