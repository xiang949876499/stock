"""港股数据连接器 - 使用 yfinance 获取港股数据"""

from datetime import date, datetime
from typing import Dict, Any, List, Optional
import asyncio

import pandas as pd
import yfinance as yf

from src.data.connectors.base import DataConnector
from src.infra.logger import get_logger

logger = get_logger("hk_stock_connector")


class HKStockConnector(DataConnector):
    """港股数据连接器

    使用 yfinance 获取港股数据，支持 quote、kline、financial 数据类型。

    股票代码格式转换:
    - 输入: "0700" 或 "0700.HK"
    - 内部: "0700.HK" (yfinance 格式)
    """

    def __init__(self):
        self._connected = False

    @property
    def name(self) -> str:
        return "hk_stock"

    @property
    def capabilities(self) -> List[str]:
        return ["quote", "kline", "financial"]

    def _normalize_symbol(self, symbol: str) -> str:
        """标准化港股代码为 yfinance 格式

        Args:
            symbol: 股票代码，如 "0700" 或 "0700.HK"

        Returns:
            yfinance 格式代码，如 "0700.HK"
        """
        symbol = symbol.strip().upper()
        if not symbol.endswith(".HK"):
            symbol = f"{symbol}.HK"
        return symbol

    async def connect(self, config: Dict[str, Any]) -> bool:
        """建立连接

        Args:
            config: 连接配置（yfinance 不需要特殊配置）

        Returns:
            是否连接成功
        """
        try:
            # yfinance 不需要显式连接，验证库可用即可
            self._connected = True
            logger.info("港股连接器初始化成功")
            return True
        except Exception as e:
            logger.error(f"港股连接器初始化失败: {e}")
            self._connected = False
            return False

    async def fetch(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """获取数据

        Args:
            query: 查询参数
                {
                    "type": "quote|kline|financial",
                    "symbol": "0700",
                    "start_date": "2024-01-01",  # kline 需要
                    "end_date": "2024-12-31",    # kline 需要
                    "period": "1d|5d|1mo|3mo|6mo|1y|2y|5y|max",  # kline 可选
                    "interval": "1d|1wk|1mo",    # kline 可选
                }

        Returns:
            数据字典
        """
        data_type = query.get("type", "quote")
        symbol = query.get("symbol", "")

        if not symbol:
            return {"error": "缺少股票代码", "success": False}

        fetchers = {
            "quote": self._fetch_quote,
            "kline": self._fetch_kline,
            "financial": self._fetch_financial,
        }

        fetcher = fetchers.get(data_type)
        if not fetcher:
            return {"error": f"不支持的数据类型: {data_type}", "success": False}

        try:
            return await fetcher(query)
        except Exception as e:
            logger.error(f"获取港股数据失败: {symbol}, {data_type}, {e}")
            return {"error": str(e), "success": False}

    async def _fetch_quote(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """获取实时行情

        Args:
            query: 查询参数

        Returns:
            行情数据字典
        """
        symbol = self._normalize_symbol(query["symbol"])

        def _get_quote():
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info or info.get("regularMarketPrice") is None:
                raise ValueError(f"无法获取 {symbol} 的行情数据")

            return {
                "success": True,
                "type": "quote",
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName", "")),
                "currency": info.get("currency", "HKD"),
                "current_price": info.get("regularMarketPrice", info.get("currentPrice", 0)),
                "previous_close": info.get("regularMarketPreviousClose", info.get("previousClose", 0)),
                "open": info.get("regularMarketOpen", info.get("open", 0)),
                "day_high": info.get("regularMarketDayHigh", info.get("dayHigh", 0)),
                "day_low": info.get("regularMarketDayLow", info.get("dayLow", 0)),
                "volume": info.get("regularMarketVolume", info.get("volume", 0)),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "pb_ratio": info.get("priceToBook", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "52w_high": info.get("fiftyTwoWeekHigh", 0),
                "52w_low": info.get("fiftyTwoWeekLow", 0),
                "avg_volume": info.get("averageVolume", 0),
                "beta": info.get("beta", 0),
                "exchange": info.get("exchange", ""),
                "timestamp": datetime.now().isoformat(),
            }

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_quote)

    async def _fetch_kline(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """获取 K 线数据

        Args:
            query: 查询参数

        Returns:
            K 线数据字典
        """
        symbol = self._normalize_symbol(query["symbol"])
        start_date = query.get("start_date")
        end_date = query.get("end_date")
        period = query.get("period", "1y")
        interval = query.get("interval", "1d")

        def _get_kline():
            ticker = yf.Ticker(symbol)

            if start_date and end_date:
                df = ticker.history(start=start_date, end=end_date, interval=interval)
            else:
                df = ticker.history(period=period, interval=interval)

            if df.empty:
                raise ValueError(f"无法获取 {symbol} 的 K 线数据")

            # 转换为标准格式
            records = []
            for idx, row in df.iterrows():
                records.append({
                    "date": idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx),
                    "open": round(float(row.get("Open", 0)), 4),
                    "high": round(float(row.get("High", 0)), 4),
                    "low": round(float(row.get("Low", 0)), 4),
                    "close": round(float(row.get("Close", 0)), 4),
                    "volume": int(row.get("Volume", 0)),
                })

            return {
                "success": True,
                "type": "kline",
                "symbol": symbol,
                "interval": interval,
                "count": len(records),
                "data": records,
            }

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_kline)

    async def _fetch_financial(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """获取财务数据

        Args:
            query: 查询参数

        Returns:
            财务数据字典
        """
        symbol = self._normalize_symbol(query["symbol"])

        def _get_financial():
            ticker = yf.Ticker(symbol)
            info = ticker.info

            if not info:
                raise ValueError(f"无法获取 {symbol} 的财务数据")

            # 获取财务报表
            financials = {}
            try:
                income_stmt = ticker.income_stmt
                if income_stmt is not None and not income_stmt.empty:
                    latest = income_stmt.iloc[:, 0]
                    financials["revenue"] = float(latest.get("Total Revenue", 0) or 0)
                    financials["net_income"] = float(latest.get("Net Income", 0) or 0)
                    financials["gross_profit"] = float(latest.get("Gross Profit", 0) or 0)
                    financials["operating_income"] = float(latest.get("Operating Income", 0) or 0)
                    financials["ebitda"] = float(latest.get("EBITDA", 0) or 0)
            except Exception as e:
                logger.warning(f"获取利润表失败: {symbol}, {e}")

            try:
                balance_sheet = ticker.balance_sheet
                if balance_sheet is not None and not balance_sheet.empty:
                    latest = balance_sheet.iloc[:, 0]
                    financials["total_assets"] = float(latest.get("Total Assets", 0) or 0)
                    financials["total_liabilities"] = float(latest.get("Total Liabilities Net Minority Interest", 0) or 0)
                    financials["total_equity"] = float(latest.get("Stockholders Equity", 0) or 0)
                    financials["cash"] = float(latest.get("Cash And Cash Equivalents", 0) or 0)
            except Exception as e:
                logger.warning(f"获取资产负债表失败: {symbol}, {e}")

            return {
                "success": True,
                "type": "financial",
                "symbol": symbol,
                "name": info.get("longName", info.get("shortName", "")),
                "currency": info.get("currency", "HKD"),
                "market_cap": info.get("marketCap", 0),
                "pe_ratio": info.get("trailingPE", 0),
                "forward_pe": info.get("forwardPE", 0),
                "pb_ratio": info.get("priceToBook", 0),
                "ps_ratio": info.get("priceToSalesTrailing12Months", 0),
                "roe": info.get("returnOnEquity", 0),
                "roa": info.get("returnOnAssets", 0),
                "profit_margin": info.get("profitMargins", 0),
                "operating_margin": info.get("operatingMargins", 0),
                "debt_to_equity": info.get("debtToEquity", 0),
                "current_ratio": info.get("currentRatio", 0),
                "dividend_yield": info.get("dividendYield", 0),
                "earnings_growth": info.get("earningsGrowth", 0),
                "revenue_growth": info.get("revenueGrowth", 0),
                "beta": info.get("beta", 0),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "employees": info.get("fullTimeEmployees", 0),
                "financials": financials,
                "timestamp": datetime.now().isoformat(),
            }

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _get_financial)

    async def disconnect(self) -> None:
        """断开连接"""
        self._connected = False
        logger.info("港股连接器已断开")

    async def health_check(self) -> bool:
        """健康检查

        Returns:
            连接器是否正常
        """
        try:
            # 尝试获取一个常见港股的行情来验证
            def _check():
                ticker = yf.Ticker("0700.HK")
                info = ticker.info
                return info is not None and len(info) > 0

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _check)
        except Exception as e:
            logger.error(f"港股连接器健康检查失败: {e}")
            return False
