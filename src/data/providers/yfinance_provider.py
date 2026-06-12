"""YFinance 数据源"""

import time
from datetime import date, datetime
from typing import Optional
import pandas as pd

from .base import DataProvider
from src.data.models import Market, StockInfo, FinancialData, NewsItem
from src.infra.logger import get_logger

logger = get_logger("yfinance")

# 请求间隔控制
_last_request_time = 0
_MIN_REQUEST_INTERVAL = 1.0


def _throttle():
    """请求节流"""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


class YFinanceProvider(DataProvider):
    """YFinance 数据源（支持 A股、港股、美股）"""

    async def fetch_daily(
        self,
        symbol: str,
        market: Market,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """获取日线数据"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                _throttle()
                import yfinance as yf

                ticker = self._to_ticker(symbol, market)
                df = yf.download(
                    ticker,
                    start=start_date.isoformat(),
                    end=end_date.isoformat(),
                    progress=False,
                    auto_adjust=True,
                )

                if df is None or df.empty:
                    raise ValueError(f"无数据: {symbol} ({ticker})")

                # 重命名列
                df = df.reset_index()
                df = df.rename(columns={
                    "Date": "date",
                    "Open": "open",
                    "High": "high",
                    "Low": "low",
                    "Close": "close",
                    "Volume": "volume",
                })

                df["date"] = pd.to_datetime(df["date"]).dt.date
                df["symbol"] = symbol
                df["market"] = market.value
                df["amount"] = df["close"] * df["volume"]
                df["turnover"] = 0.0
                df["adj_factor"] = 1.0

                return df[["date", "open", "high", "low", "close", "volume", "amount", "turnover", "adj_factor", "symbol", "market"]]

            except Exception as e:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 3
                    logger.warning(f"获取日线数据失败，{wait}秒后重试 ({attempt+1}/{max_retries}): {symbol}, {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"获取日线数据失败: {symbol}, {market}, {e}")
                    raise

    async def fetch_stock_info(
        self,
        symbol: str,
        market: Market
    ) -> StockInfo:
        """获取股票基本信息"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                _throttle()
                import yfinance as yf

                ticker = self._to_ticker(symbol, market)
                stock = yf.Ticker(ticker)
                info = stock.info

                if not info:
                    raise ValueError(f"未找到股票: {symbol} ({ticker})")

                return StockInfo(
                    symbol=symbol,
                    name=info.get("shortName", info.get("longName", symbol)),
                    market=market,
                    industry=info.get("industry", ""),
                    list_date=self._parse_date(info.get("firstTradeDateEpochUtc")),
                    is_st=False,
                    is_active=True,
                )

            except Exception as e:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 3
                    logger.warning(f"获取股票信息失败，{wait}秒后重试 ({attempt+1}/{max_retries}): {symbol}, {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"获取股票信息失败: {symbol}, {market}, {e}")
                    raise

    async def fetch_financial(
        self,
        symbol: str,
        market: Market
    ) -> FinancialData:
        """获取财务数据"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                _throttle()
                import yfinance as yf

                ticker = self._to_ticker(symbol, market)
                stock = yf.Ticker(ticker)

                # 获取财务数据
                financials = stock.financials
                info = stock.info

                revenue = 0.0
                net_profit = 0.0
                report_date = date.today()

                if financials is not None and not financials.empty:
                    latest = financials.iloc[:, 0]
                    revenue = float(latest.get("Total Revenue", 0) or 0)
                    net_profit = float(latest.get("Net Income", 0) or 0)
                    if hasattr(financials.columns[0], 'date'):
                        report_date = financials.columns[0].date()

                return FinancialData(
                    symbol=symbol,
                    market=market,
                    report_date=report_date,
                    revenue=revenue,
                    net_profit=net_profit,
                    eps=float(info.get("trailingEps", 0) or 0),
                    roe=float(info.get("returnOnEquity", 0) or 0) * 100 if info.get("returnOnEquity") else 0.0,
                    pe_ratio=float(info.get("trailingPE", 0) or 0),
                    pb_ratio=float(info.get("priceToBook", 0) or 0),
                )

            except Exception as e:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 3
                    logger.warning(f"获取财务数据失败，{wait}秒后重试 ({attempt+1}/{max_retries}): {symbol}, {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"获取财务数据失败: {symbol}, {market}, {e}")
                    raise

    async def fetch_news(
        self,
        symbol: str,
        market: Market,
        limit: int = 50
    ) -> list[NewsItem]:
        """获取新闻数据"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                _throttle()
                import yfinance as yf

                ticker = self._to_ticker(symbol, market)
                stock = yf.Ticker(ticker)
                news = stock.news

                if not news:
                    return []

                news_list = []
                for item in news[:limit]:
                    content = item.get("content", {})
                    news_list.append(NewsItem(
                        id=str(item.get("uuid", "")),
                        symbol=symbol,
                        market=market,
                        title=content.get("title", item.get("title", "")),
                        content=content.get("summary", item.get("summary", "")),
                        source=content.get("provider", {}).get("displayName", "yfinance"),
                        url=content.get("canonicalUrl", {}).get("url", item.get("link", "")),
                        publish_time=datetime.fromtimestamp(item.get("providerPublishTime", 0)) if item.get("providerPublishTime") else datetime.now(),
                        sentiment="neutral",
                        importance="P2",
                    ))

                return news_list

            except Exception as e:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 3
                    logger.warning(f"获取新闻失败，{wait}秒后重试 ({attempt+1}/{max_retries}): {symbol}, {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"获取新闻失败: {symbol}, {market}, {e}")
                    raise

    def _to_ticker(self, symbol: str, market: Market) -> str:
        """转换为 YFinance ticker 格式"""
        if market == Market.HK:
            # 港股：00700 → 0700.HK
            return f"{symbol.lstrip('0')}.HK" if symbol else f"{symbol}.HK"
        elif market == Market.US:
            # 美股：直接使用
            return symbol
        else:
            # A股：600519 → 600519.SS（上海）或 000001 → 000001.SZ（深圳）
            if symbol.startswith("6"):
                return f"{symbol}.SS"
            return f"{symbol}.SZ"

    def _parse_date(self, epoch) -> date:
        """解析 epoch 时间戳为日期"""
        if not epoch:
            return date.today()
        try:
            return datetime.fromtimestamp(int(epoch)).date()
        except (ValueError, TypeError, OSError):
            return date.today()
