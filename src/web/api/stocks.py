"""股票 API"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from src.data.models import Market, StockInfo
from src.data.service import DataService
from src.infra.logger import get_logger

logger = get_logger("stocks_api")

router = APIRouter(prefix="/stocks", tags=["stocks"])

# 数据服务实例（延迟初始化）
_data_service: Optional[DataService] = None


def get_data_service() -> DataService:
    """获取数据服务"""
    global _data_service
    if _data_service is None:
        _data_service = DataService()
    return _data_service


@router.get("/")
async def list_stocks(market: Optional[str] = Query(None)):
    """获取股票列表"""
    try:
        service = get_data_service()
        # 从 catalog 获取股票列表
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}")
async def get_stock(symbol: str, market: str = Query("A")):
    """获取股票详情"""
    try:
        service = get_data_service()
        market_enum = Market(market)

        # 从 catalog 获取信息
        catalog_info = service.catalog.mapping.get(symbol, {})

        return {
            "symbol": symbol,
            "name": catalog_info.get("name", ""),
            "market": market,
            "industry": catalog_info.get("industry", ""),
            "is_active": True,
        }
    except Exception as e:
        logger.error(f"获取股票详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/kline")
async def get_kline(
    symbol: str,
    market: str = Query("A"),
    period: str = Query("daily"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """获取 K 线数据"""
    try:
        from datetime import date
        service = get_data_service()
        market_enum = Market(market)

        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None

        df = await service.get_daily(symbol, market_enum, start, end)

        if df is None or df.empty:
            return []

        # 转换为列表
        records = df.to_dict(orient="records")
        return records
    except Exception as e:
        logger.error(f"获取 K 线数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/technical")
async def get_technical(symbol: str, market: str = Query("A")):
    """获取技术指标"""
    try:
        service = get_data_service()
        market_enum = Market(market)
        indicators = await service.get_technical_indicators(symbol, market_enum)
        return indicators
    except Exception as e:
        logger.error(f"获取技术指标失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
