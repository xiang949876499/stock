"""组合数据源 — 支持多数据源 fallback"""

from datetime import date
from typing import Optional
import pandas as pd

from .base import DataProvider
from src.data.models import Market, StockInfo, FinancialData, NewsItem
from src.infra.logger import get_logger

logger = get_logger("composite")


class CompositeProvider(DataProvider):
    """组合数据源：按优先级依次尝试多个 provider，失败自动 fallback"""

    def __init__(self, providers: list[DataProvider]):
        """
        Args:
            providers: 按优先级排列的数据源列表，第一个为主数据源
        """
        if not providers:
            raise ValueError("至少需要一个数据源")
        self.providers = providers
        self._names = [type(p).__name__ for p in providers]
        logger.info(f"组合数据源初始化: {' → '.join(self._names)}")

    async def fetch_daily(
        self,
        symbol: str,
        market: Market,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """获取日线数据（自动 fallback）"""
        return await self._try_all(
            "fetch_daily",
            lambda p: p.fetch_daily(symbol, market, start_date, end_date)
        )

    async def fetch_stock_info(
        self,
        symbol: str,
        market: Market
    ) -> StockInfo:
        """获取股票基本信息（自动 fallback）"""
        return await self._try_all(
            "fetch_stock_info",
            lambda p: p.fetch_stock_info(symbol, market)
        )

    async def fetch_financial(
        self,
        symbol: str,
        market: Market
    ) -> FinancialData:
        """获取财务数据（自动 fallback）"""
        return await self._try_all(
            "fetch_financial",
            lambda p: p.fetch_financial(symbol, market)
        )

    async def fetch_news(
        self,
        symbol: str,
        market: Market,
        limit: int = 50
    ) -> list[NewsItem]:
        """获取新闻数据（自动 fallback）"""
        return await self._try_all(
            "fetch_news",
            lambda p: p.fetch_news(symbol, market, limit)
        )

    async def _try_all(self, method: str, call):
        """依次尝试所有 provider，返回第一个成功的结果"""
        errors = []
        for i, provider in enumerate(self.providers):
            name = self._names[i]
            try:
                result = await call(provider)
                if i > 0:
                    logger.info(f"[fallback] {method} 成功: {name}")
                return result
            except NotImplementedError:
                logger.debug(f"[skip] {name}.{method} 未实现")
                errors.append(f"{name}: 未实现")
            except Exception as e:
                logger.warning(f"[fallback] {name}.{method} 失败: {e}")
                errors.append(f"{name}: {e}")

        raise RuntimeError(f"所有数据源均失败: {'; '.join(errors)}")
