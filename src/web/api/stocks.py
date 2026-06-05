"""股票 API"""

from fastapi import APIRouter, Query, Depends
from typing import Optional

from src.data.models import Market
from src.data.service import DataService
from src.web.deps import get_data_service
from src.exceptions import NotFoundError, DataProviderError
from src.infra.logger import get_logger

logger = get_logger("stocks_api")

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/")
async def list_stocks(
    market: Optional[str] = Query(None),
    service: DataService = Depends(get_data_service),
):
    """获取股票列表"""
    try:
        stocks = []
        for symbol, info in service.catalog.mapping.items():
            if market is None or info.get("market") == market:
                stocks.append({
                    "symbol": symbol,
                    "name": info.get("name", ""),
                    "market": info.get("market", "A"),
                    "industry": info.get("industry", ""),
                    "is_active": True,
                })
        return stocks
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise DataProviderError(f"获取股票列表失败: {e}")


@router.get("/{symbol}")
async def get_stock(
    symbol: str,
    market: str = Query("A"),
    service: DataService = Depends(get_data_service),
):
    """获取股票详情"""
    try:
        catalog_info = service.catalog.mapping.get(symbol)
        if not catalog_info:
            raise NotFoundError(f"股票 {symbol} 不存在")

        return {
            "symbol": symbol,
            "name": catalog_info.get("name", ""),
            "market": market,
            "industry": catalog_info.get("industry", ""),
            "is_active": True,
        }
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"获取股票详情失败: {e}")
        raise DataProviderError(f"获取股票详情失败: {e}")


@router.get("/{symbol}/kline")
async def get_kline(
    symbol: str,
    market: str = Query("A"),
    period: str = Query("daily"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    service: DataService = Depends(get_data_service),
):
    """获取 K 线数据"""
    try:
        from datetime import date

        market_enum = Market(market)
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None

        df = await service.get_daily(symbol, market_enum, start, end)

        if df is None or df.empty:
            return []

        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"获取 K 线数据失败: {e}")
        raise DataProviderError(f"获取 K 线数据失败: {e}")


@router.get("/{symbol}/technical")
async def get_technical(
    symbol: str,
    market: str = Query("A"),
    service: DataService = Depends(get_data_service),
):
    """获取技术指标"""
    try:
        market_enum = Market(market)
        indicators = await service.get_technical_indicators(symbol, market_enum)
        return indicators
    except Exception as e:
        logger.error(f"获取技术指标失败: {e}")
        raise DataProviderError(f"获取技术指标失败: {e}")
