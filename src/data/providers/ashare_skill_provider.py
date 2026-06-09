"""a-share-skill 数据源适配器"""

import os
import sys
from datetime import date, datetime
from typing import Optional
import pandas as pd

# 禁用代理
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

from .base import DataProvider
from src.data.models import Market, StockInfo, FinancialData, NewsItem
from src.infra.logger import get_logger

logger = get_logger("ashare_skill")

# a-share-skill 路径
ASHARE_SKILL_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'a-share-skill', 'a-share-data', 'scripts')

# 添加到 Python 路径
if ASHARE_SKILL_PATH not in sys.path:
    sys.path.insert(0, ASHARE_SKILL_PATH)


class AShareSkillProvider(DataProvider):
    """a-share-skill 数据源"""

    def __init__(self):
        self._initialized = False
        self._fetch_realtime = None
        self._fetch_history = None
        self._fetch_technical = None

    def _init_modules(self):
        """延迟初始化模块"""
        if self._initialized:
            return

        try:
            # 动态导入 a-share-skill 模块
            import importlib.util

            # 导入 fetch_realtime
            spec = importlib.util.spec_from_file_location(
                "fetch_realtime",
                os.path.join(ASHARE_SKILL_PATH, "fetch_realtime.py")
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._fetch_realtime = module

            # 导入 fetch_history
            spec = importlib.util.spec_from_file_location(
                "fetch_history",
                os.path.join(ASHARE_SKILL_PATH, "fetch_history.py")
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._fetch_history = module

            # 导入 fetch_technical
            spec = importlib.util.spec_from_file_location(
                "fetch_technical",
                os.path.join(ASHARE_SKILL_PATH, "fetch_technical.py")
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self._fetch_technical = module

            self._initialized = True
            logger.info("a-share-skill 模块加载成功")

        except Exception as e:
            logger.error(f"a-share-skill 模块加载失败: {e}")
            self._initialized = True  # 标记为已初始化，避免重复尝试

    async def fetch_daily(
        self,
        symbol: str,
        market: Market,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """获取日线数据"""
        self._init_modules()

        try:
            if market != Market.A:
                raise ValueError(f"a-share-skill 仅支持 A 股，不支持: {market}")

            # 使用 a-share-skill 获取历史数据
            if self._fetch_history:
                df = self._fetch_history.fetch_history(
                    symbol=symbol,
                    start_date=start_date.strftime("%Y%m%d"),
                    end_date=end_date.strftime("%Y%m%d"),
                    period="daily"
                )

                if df is not None and not df.empty:
                    # 统一列名
                    df = self._normalize_columns(df)
                    df["symbol"] = symbol
                    df["market"] = market.value
                    df["adj_factor"] = 1.0
                    return df

            raise ValueError("fetch_history 模块未加载")

        except Exception as e:
            logger.error(f"获取日线数据失败: {symbol}, {market}, {e}")
            raise

    async def fetch_realtime(self, symbols: list[str]) -> list[dict]:
        """获取实时行情"""
        self._init_modules()

        try:
            if self._fetch_realtime:
                results = []
                for symbol in symbols:
                    data = self._fetch_realtime.fetch_realtime(symbol)
                    if data:
                        results.append(data)
                return results

            raise ValueError("fetch_realtime 模块未加载")

        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            raise

    async def fetch_technical(
        self,
        symbol: str,
        indicators: list[str] = None
    ) -> dict:
        """获取技术指标"""
        self._init_modules()

        try:
            if self._fetch_technical:
                if indicators is None:
                    indicators = ["ma", "macd", "kdj", "rsi", "boll"]

                result = self._fetch_technical.fetch_technical(
                    symbol=symbol,
                    indicators=indicators
                )
                return result

            raise ValueError("fetch_technical 模块未加载")

        except Exception as e:
            logger.error(f"获取技术指标失败: {symbol}, {e}")
            raise

    async def fetch_stock_info(
        self,
        symbol: str,
        market: Market
    ) -> StockInfo:
        """获取股票基本信息"""
        # 使用缓存的 catalog 信息
        from src.data.catalog.manager import InstrumentCatalog
        catalog = InstrumentCatalog()

        info = catalog.mapping.get(symbol, {})
        return StockInfo(
            symbol=symbol,
            name=info.get("name", symbol),
            market=market,
            industry=info.get("industry", ""),
            list_date=date(2020, 1, 1),  # 默认日期
            is_st=False,
            is_active=True,
        )

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

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """统一列名"""
        column_mapping = {
            "日期": "date",
            "date": "date",
            "开盘": "open",
            "open": "open",
            "最高": "high",
            "high": "high",
            "最低": "low",
            "low": "low",
            "收盘": "close",
            "close": "close",
            "成交量": "volume",
            "volume": "volume",
            "成交额": "amount",
            "amount": "amount",
            "换手率": "turnover",
            "turnover": "turnover",
        }

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 确保日期列存在
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date

        return df
