"""AkShare 数据源"""

from datetime import date, datetime
from typing import Optional
import os
import pandas as pd

# 禁用代理访问国内数据源
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

import akshare as ak

from .base import DataProvider
from src.data.models import Market, StockInfo, FinancialData, NewsItem
from src.infra.logger import get_logger

logger = get_logger("akshare")


class AkShareProvider(DataProvider):
    """AkShare 数据源"""

    async def fetch_daily(
        self,
        symbol: str,
        market: Market,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """获取日线数据"""
        try:
            if market == Market.A:
                # A股日线数据
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date.strftime("%Y%m%d"),
                    end_date=end_date.strftime("%Y%m%d"),
                    adjust="hfq"  # 后复权
                )
                # 重命名列
                df = df.rename(columns={
                    "日期": "date",
                    "开盘": "open",
                    "最高": "high",
                    "最低": "low",
                    "收盘": "close",
                    "成交量": "volume",
                    "成交额": "amount",
                    "换手率": "turnover",
                })
                df["symbol"] = symbol
                df["market"] = market.value
                df["adj_factor"] = 1.0
                return df
            elif market == Market.HK:
                # 港股日线数据
                df = ak.stock_hk_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date.strftime("%Y%m%d"),
                    end_date=end_date.strftime("%Y%m%d"),
                    adjust="hfq"
                )
                df = df.rename(columns={
                    "日期": "date",
                    "开盘": "open",
                    "最高": "high",
                    "最低": "low",
                    "收盘": "close",
                    "成交量": "volume",
                    "成交额": "amount",
                    "换手率": "turnover",
                })
                df["symbol"] = symbol
                df["market"] = market.value
                df["adj_factor"] = 1.0
                return df
            else:
                raise ValueError(f"不支持的市场: {market}")
        except Exception as e:
            logger.error(f"获取日线数据失败: {symbol}, {market}, {e}")
            raise

    async def fetch_stock_info(
        self,
        symbol: str,
        market: Market
    ) -> StockInfo:
        """获取股票基本信息"""
        try:
            if market == Market.A:
                # A股基本信息
                df = ak.stock_info_a_code_name()
                stock = df[df["code"] == symbol].iloc[0]
                return StockInfo(
                    symbol=symbol,
                    name=stock["name"],
                    market=market,
                    industry="",
                    list_date=date.today(),
                    is_st=False,
                    is_active=True,
                )
            else:
                raise ValueError(f"不支持的市场: {market}")
        except Exception as e:
            logger.error(f"获取股票信息失败: {symbol}, {market}, {e}")
            raise

    async def fetch_financial(
        self,
        symbol: str,
        market: Market
    ) -> FinancialData:
        """获取财务数据"""
        # TODO: 实现财务数据获取
        raise NotImplementedError("财务数据获取未实现")

    async def fetch_news(
        self,
        symbol: str,
        market: Market,
        limit: int = 50
    ) -> list[NewsItem]:
        """获取新闻数据"""
        # TODO: 实现新闻数据获取
        raise NotImplementedError("新闻数据获取未实现")
