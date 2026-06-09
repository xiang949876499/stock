"""数据源基类"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
import pandas as pd

from src.data.models import Market, StockDaily, StockInfo, FinancialData, NewsItem


class DataProvider(ABC):
    """数据源基类"""

    @abstractmethod
    async def fetch_daily(
        self,
        symbol: str,
        market: Market,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """获取日线数据"""
        pass

    @abstractmethod
    async def fetch_stock_info(
        self,
        symbol: str,
        market: Market
    ) -> StockInfo:
        """获取股票基本信息"""
        pass

    @abstractmethod
    async def fetch_financial(
        self,
        symbol: str,
        market: Market
    ) -> FinancialData:
        """获取财务数据"""
        pass

    @abstractmethod
    async def fetch_news(
        self,
        symbol: str,
        market: Market,
        limit: int = 50
    ) -> list[NewsItem]:
        """获取新闻数据"""
        pass
