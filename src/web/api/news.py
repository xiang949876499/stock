"""新闻 API"""

from fastapi import APIRouter, Query, Depends
from typing import Optional

from src.data.models import Market
from src.news.service import NewsService
from src.web.deps import get_news_service
from src.exceptions import DataProviderError
from src.infra.logger import get_logger

logger = get_logger("news_api")

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/")
async def list_news(
    symbol: Optional[str] = Query(None),
    market: Optional[str] = Query(None, pattern="^(A|HK|US)$"),
    sentiment: Optional[str] = Query(None, pattern="^(positive|negative|neutral)$"),
    days: int = Query(7, ge=1, le=30),
    service: NewsService = Depends(get_news_service),
):
    """获取新闻列表"""
    try:
        if symbol and market:
            market_enum = Market(market)
            news = await service.get_news(symbol, market_enum, limit=50)

            # 过滤情绪
            if sentiment:
                news = [n for n in news if n.sentiment == sentiment]

            return news
        return []
    except Exception as e:
        logger.error(f"获取新闻失败: {e}")
        raise DataProviderError(f"获取新闻失败: {e}")


@router.get("/sentiment")
async def get_sentiment(
    symbol: str = Query(..., min_length=1, max_length=10),
    market: str = Query("A", pattern="^(A|HK|US)$"),
    days: int = Query(30, ge=1, le=90),
    service: NewsService = Depends(get_news_service),
):
    """获取舆情分析"""
    try:
        market_enum = Market(market)
        sentiment = await service.get_sentiment(symbol, market_enum, days)
        return sentiment
    except Exception as e:
        logger.error(f"获取舆情分析失败: {e}")
        raise DataProviderError(f"获取舆情分析失败: {e}")


@router.get("/hot")
async def get_hot_news(
    market: str = Query("A", pattern="^(A|HK|US)$"),
    limit: int = Query(20, ge=1, le=100),
    service: NewsService = Depends(get_news_service),
):
    """获取热门新闻"""
    try:
        market_enum = Market(market)
        news = await service.get_hot_news(market_enum, limit)
        return news
    except Exception as e:
        logger.error(f"获取热门新闻失败: {e}")
        raise DataProviderError(f"获取热门新闻失败: {e}")
