"""新闻服务"""

from typing import Optional
from src.data.models import Market, NewsItem
from src.news.collectors.base import NewsCollector
from src.news.collectors.eastmoney import EastMoneyCollector
from src.news.processors.dedup import deduplicate_news
from src.news.processors.classify import classify_sentiment, classify_importance
from src.news.processors.sentiment import analyze_sentiment
from src.news.processors.entity import extract_entities
from src.news.analysis.analyzer import NewsAnalyzer
from src.infra.logger import get_logger

logger = get_logger("news_service")


class NewsService:
    """新闻服务"""

    def __init__(
        self,
        collectors: Optional[list[NewsCollector]] = None,
    ):
        self.collectors = collectors or [EastMoneyCollector()]
        self.analyzer = NewsAnalyzer()

    async def get_news(
        self,
        symbol: str,
        market: Market,
        limit: int = 50
    ) -> list[NewsItem]:
        """获取新闻"""
        all_news = []

        # 从所有采集器获取新闻
        for collector in self.collectors:
            try:
                news = await collector.collect(symbol, market, limit)
                all_news.extend(news)
            except Exception as e:
                logger.error(f"新闻采集失败: {e}")

        # 去重
        unique_news = deduplicate_news(all_news)

        # 分类
        for news in unique_news:
            news.sentiment = classify_sentiment(news)
            news.importance = classify_importance(news)

        # 按时间排序
        unique_news.sort(key=lambda x: x.publish_time, reverse=True)

        return unique_news[:limit]

    async def get_sentiment(
        self,
        symbol: str,
        market: Market,
        days: int = 30
    ) -> dict:
        """获取舆情分析"""
        # 获取新闻
        news_list = await self.get_news(symbol, market, limit=100)

        # 分析舆情
        return self.analyzer.analyze(news_list)

    async def get_hot_news(
        self,
        market: Market,
        limit: int = 20
    ) -> list[NewsItem]:
        """获取热门新闻"""
        # TODO: 实现热门新闻获取
        return []

    async def search_news(
        self,
        keyword: str,
        market: Market,
        limit: int = 50
    ) -> list[NewsItem]:
        """搜索新闻"""
        # TODO: 实现新闻搜索
        return []
