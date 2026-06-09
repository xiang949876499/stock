"""westock-data-skillhub 数据源适配器"""

import os
import subprocess
import json
from datetime import date, datetime
from typing import Optional
import pandas as pd

from .base import DataProvider
from src.data.models import Market, StockInfo, FinancialData, NewsItem
from src.infra.logger import get_logger

logger = get_logger("westock")


class WestockProvider(DataProvider):
    """westock-data-skillhub 数据源"""

    def __init__(self):
        self.command = "npx westock-data-skillhub"

    def _run_command(self, args: list[str]) -> dict:
        """运行命令"""
        try:
            cmd = f"{self.command} {' '.join(args)}"
            logger.info(f"执行命令: {cmd}")

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )

            if result.returncode == 0:
                output = result.stdout
                # 尝试解析 JSON
                try:
                    return json.loads(output)
                except json.JSONDecodeError:
                    return {"raw": output}
            else:
                logger.error(f"命令执行失败: {result.stderr}")
                return {"error": result.stderr}

        except subprocess.TimeoutExpired:
            logger.error("命令执行超时")
            return {"error": "timeout"}
        except Exception as e:
            logger.error(f"命令执行异常: {e}")
            return {"error": str(e)}

    def _format_symbol(self, symbol: str, market: Market) -> str:
        """格式化股票代码"""
        if market == Market.A:
            # A 股：添加市场前缀
            if symbol.startswith("6"):
                return f"sh{symbol}"
            else:
                return f"sz{symbol}"
        elif market == Market.HK:
            # 港股：添加前缀
            return f"hk{symbol}"
        return symbol

    async def fetch_daily(
        self,
        symbol: str,
        market: Market,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """获取日线数据"""
        try:
            formatted_symbol = self._format_symbol(symbol, market)

            # 计算天数
            days = (end_date - start_date).days

            result = self._run_command([
                "kline",
                formatted_symbol,
                "--period", "daily",
                "--limit", str(days)
            ])

            if "error" in result:
                raise ValueError(result["error"])

            if "data" in result and result["data"]:
                df = pd.DataFrame(result["data"])
                df = self._normalize_columns(df)
                df["symbol"] = symbol
                df["market"] = market.value
                df["adj_factor"] = 1.0
                return df

            raise ValueError("无数据")

        except Exception as e:
            logger.error(f"获取日线数据失败: {symbol}, {market}, {e}")
            raise

    async def fetch_realtime(self, symbols: list[str], market: Market = Market.A) -> list[dict]:
        """获取实时行情"""
        try:
            formatted_symbols = [self._format_symbol(s, market) for s in symbols]
            symbols_str = ",".join(formatted_symbols)

            result = self._run_command([
                "kline",
                symbols_str,
                "--limit", "1"
            ])

            if "error" in result:
                raise ValueError(result["error"])

            if "data" in result:
                return result["data"]

            return []

        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            raise

    async def fetch_technical(
        self,
        symbol: str,
        market: Market = Market.A,
        group: str = "all"
    ) -> dict:
        """获取技术指标"""
        try:
            formatted_symbol = self._format_symbol(symbol, market)

            result = self._run_command([
                "technical",
                formatted_symbol,
                "--group", group
            ])

            if "error" in result:
                raise ValueError(result["error"])

            return result

        except Exception as e:
            logger.error(f"获取技术指标失败: {symbol}, {e}")
            raise

    async def fetch_finance(
        self,
        symbol: str,
        market: Market = Market.A,
        finance_type: str = "all"
    ) -> dict:
        """获取财务数据"""
        try:
            formatted_symbol = self._format_symbol(symbol, market)

            result = self._run_command([
                "finance",
                formatted_symbol,
                "--type", finance_type
            ])

            if "error" in result:
                raise ValueError(result["error"])

            return result

        except Exception as e:
            logger.error(f"获取财务数据失败: {symbol}, {e}")
            raise

    async def fetch_stock_info(
        self,
        symbol: str,
        market: Market
    ) -> StockInfo:
        """获取股票基本信息"""
        try:
            formatted_symbol = self._format_symbol(symbol, market)

            result = self._run_command([
                "profile",
                formatted_symbol
            ])

            if "error" in result:
                # 使用 catalog 信息
                from src.data.catalog.manager import InstrumentCatalog
                catalog = InstrumentCatalog()
                info = catalog.mapping.get(symbol, {})
                return StockInfo(
                    symbol=symbol,
                    name=info.get("name", symbol),
                    market=market,
                    industry=info.get("industry", ""),
                    list_date=date(2020, 1, 1),
                    is_st=False,
                    is_active=True,
                )

            # 解析结果
            data = result.get("data", [{}])[0] if "data" in result else {}
            return StockInfo(
                symbol=symbol,
                name=data.get("name", symbol),
                market=market,
                industry=data.get("industry", ""),
                list_date=date(2020, 1, 1),
                is_st=False,
                is_active=True,
            )

        except Exception as e:
            logger.error(f"获取股票信息失败: {symbol}, {e}")
            raise

    async def fetch_financial(
        self,
        symbol: str,
        market: Market
    ) -> FinancialData:
        """获取财务数据"""
        raise NotImplementedError("财务数据获取未实现")

    async def fetch_news(
        self,
        symbol: str,
        market: Market,
        limit: int = 50
    ) -> list[NewsItem]:
        """获取新闻数据"""
        raise NotImplementedError("新闻数据获取未实现")

    async def search(self, keyword: str) -> list[dict]:
        """搜索股票"""
        try:
            result = self._run_command(["search", keyword, "--stock"])

            if "error" in result:
                return []

            # 解析表格输出
            raw = result.get("raw", "")
            lines = raw.strip().split("\n")

            stocks = []
            for line in lines[2:]:  # 跳过表头
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2:
                    code = parts[0].replace("sh", "").replace("sz", "").replace("hk", "")
                    stocks.append({
                        "code": code,
                        "name": parts[1],
                        "type": parts[2] if len(parts) > 2 else ""
                    })

            return stocks

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    async def fetch_hot(self, hot_type: str = "stock", limit: int = 10) -> list[dict]:
        """获取热搜"""
        try:
            result = self._run_command(["hot", hot_type, "--limit", str(limit)])

            if "error" in result:
                return []

            if "data" in result:
                return result["data"]

            return []

        except Exception as e:
            logger.error(f"获取热搜失败: {e}")
            return []

    async def fetch_lhb(self, symbol: str, market: Market = Market.A, trade_date: str = None) -> dict:
        """获取龙虎榜"""
        try:
            formatted_symbol = self._format_symbol(symbol, market)

            args = ["lhb", formatted_symbol]
            if trade_date:
                args.extend(["--date", trade_date])

            result = self._run_command(args)

            if "error" in result:
                raise ValueError(result["error"])

            return result

        except Exception as e:
            logger.error(f"获取龙虎榜失败: {symbol}, {e}")
            raise

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """统一列名"""
        column_mapping = {
            "date": "date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "amount": "amount",
            "turnover": "turnover",
        }

        df = df.rename(columns=column_mapping)

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date

        return df
