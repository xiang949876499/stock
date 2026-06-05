"""新闻 API"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from src.data.models import Market
from src.news.service import NewsService
from src.infra.logger import get_logger

logger = get_logger("news_api")

router = APIRouter(prefix="/news", tags=["news"])

# 新闻服务实例（延迟初始化）
_news_service: Optional[NewsService] = None


def get_news_service() -> NewsService:
    """获取新闻服务"""
    global _news_service
    if _news_service is None:
        _news_service = NewsService()
    return _news_service


@router.get("/")
async def list_news(
    symbol: Optional[str] = Query(None),
    market: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=30),
):
    """获取新闻列表"""
    try:
        if symbol and market:
            service = get_news_service()
            market_enum = Market(market)
            news = await service.get_news(symbol, market_enum, limit=50)

            # 过滤情绪
            if sentiment:
                news = [n for n in news if n.sentiment == sentiment]

            return news
        return []
    except Exception as e:
        logger.error(f"获取新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment")
async def get_sentiment(
    symbol: str = Query(...),
    market: str = Query("A"),
    days: int = Query(30, ge=1, le=90),
):
    """获取舆情分析"""
    try:
        service = get_news_service()
        market_enum = Market(market)
        sentiment = await service.get_sentiment(symbol, market_enum, days)
        return sentiment
    except Exception as e:
        logger.error(f"获取舆情分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot")
async def get_hot_news(
    market: str = Query("A"),
    limit: int = Query(20, ge=1, le=100),
):
    """获取热门新闻"""
    try:
        service = get_news_service()
        market_enum = Market(market)
        news = await service.get_hot_news(market_enum, limit)
        return news
    except Exception as e:
        logger.error(f"获取热门新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
