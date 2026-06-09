"""YFinance 数据源"""

from datetime import date
import pandas as pd

from .base import DataProvider
from src.data.models import Market, StockInfo, FinancialData, NewsItem
from src.infra.logger import get_logger

logger = get_logger("yfinance")


class YFinanceProvider(DataProvider):
    """YFinance 数据源"""

    async def fetch_daily(
        self,
        symbol: str,
        market: Market,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """获取日线数据"""
        # TODO: 实现 YFinance 数据获取
        raise NotImplementedError("YFinance 数据获取未实现")

    async def fetch_stock_info(
        self,
        symbol: str,
        market: Market
    ) -> StockInfo:
        """获取股票基本信息"""
        raise NotImplementedError("YFinance 数据获取未实现")

    async def fetch_financial(
        self,
        symbol: str,
        market: Market
    ) -> FinancialData:
        """获取财务数据"""
        raise NotImplementedError("YFinance 数据获取未实现")

    async def fetch_news(
        self,
        symbol: str,
        market: Market,
        limit: int = 50
    ) -> list[NewsItem]:
        """获取新闻数据"""
        raise NotImplementedError("YFinance 数据获取未实现")
