"""数据服务"""

from datetime import date
from typing import Optional
import pandas as pd

from src.data.models import Market, StockInfo, FinancialData, NewsItem, TechnicalIndicators
from src.data.providers.base import DataProvider
from src.data.providers.akshare_provider import AkShareProvider
from src.data.catalog.manager import InstrumentCatalog
from src.data.storage.parquet import ParquetStorage
from src.data.sync.manager import DataSyncManager
from src.infra.cache import LRUCache
from src.infra.logger import get_logger

logger = get_logger("data_service")


class DataService:
    """数据服务"""

    def __init__(
        self,
        provider: Optional[DataProvider] = None,
        catalog: Optional[InstrumentCatalog] = None,
        storage: Optional[ParquetStorage] = None,
    ):
        """初始化数据服务"""
        self.provider = provider or AkShareProvider()
        self.catalog = catalog or InstrumentCatalog()
        self.storage = storage or ParquetStorage()
        self.sync_manager = DataSyncManager(self.provider, self.storage)
        self.cache = LRUCache(max_size=100, ttl=300)  # 5 分钟缓存

    async def get_stock_info(
        self,
        symbol: str,
        market: Market
    ) -> StockInfo:
        """获取股票信息"""
        cache_key = f"stock_info:{symbol}:{market}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        info = await self.provider.fetch_stock_info(symbol, market)
        self.cache.set(cache_key, info)
        return info

    async def get_daily(
        self,
        symbol: str,
        market: Market,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """获取日线数据"""
        # 先从本地加载
        df = self.storage.load_daily(
            symbol, market,
            start_date.isoformat() if start_date else None,
            end_date.isoformat() if end_date else None
        )

        if df is None or df.empty:
            # 本地没有，从数据源获取
            if start_date is None:
                start_date = date(2020, 1, 1)
            if end_date is None:
                end_date = date.today()

            try:
                df = await self.provider.fetch_daily(symbol, market, start_date, end_date)

                if df is not None and not df.empty:
                    # 保存到本地
                    self.storage.save_daily(df, symbol, market)
            except Exception as e:
                logger.error(f"获取日线数据失败: {symbol}, {market}, {e}")
                return pd.DataFrame()

        return df

    async def get_financial(
        self,
        symbol: str,
        market: Market
    ) -> FinancialData:
        """获取财务数据"""
        return await self.provider.fetch_financial(symbol, market)

    async def get_news(
        self,
        symbol: str,
        market: Market,
        limit: int = 50
    ) -> list[NewsItem]:
        """获取新闻数据"""
        return await self.provider.fetch_news(symbol, market, limit)

    async def get_technical_indicators(
        self,
        symbol: str,
        market: Market
    ) -> TechnicalIndicators:
        """获取技术指标"""
        cache_key = f"technical:{symbol}:{market}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        # 获取日线数据
        df = await self.get_daily(symbol, market)

        if df is None or df.empty:
            raise ValueError(f"无法获取日线数据: {symbol}")

        # 计算技术指标
        import pandas_ta as ta

        # MA
        df["ma5"] = df["close"].rolling(window=5).mean()
        df["ma10"] = df["close"].rolling(window=10).mean()
        df["ma20"] = df["close"].rolling(window=20).mean()
        df["ma60"] = df["close"].rolling(window=60).mean()

        # MACD
        macd = ta.macd(df["close"])
        if macd is not None and not macd.empty:
            df["macd"] = macd["MACD_12_26_9"]
            df["macd_signal"] = macd["MACDs_12_26_9"]
            df["macd_hist"] = macd["MACDh_12_26_9"]

        # KDJ
        stoch = ta.stoch(df["high"], df["low"], df["close"])
        if stoch is not None and not stoch.empty:
            df["kdj_k"] = stoch["STOCHk_14_3_3"]
            df["kdj_d"] = stoch["STOCHd_14_3_3"]
            df["kdj_j"] = 3 * df["kdj_k"] - 2 * df["kdj_d"]

        # RSI
        df["rsi_6"] = ta.rsi(df["close"], length=6)
        df["rsi_12"] = ta.rsi(df["close"], length=12)
        df["rsi_24"] = ta.rsi(df["close"], length=24)

        # BOLL
        try:
            bbands = ta.bbands(df["close"], length=20, std=2)
            if bbands is not None and not bbands.empty:
                # 动态获取列名
                boll_cols = bbands.columns.tolist()
                for col in boll_cols:
                    if 'BBU' in col:
                        df["boll_upper"] = bbands[col]
                    elif 'BBM' in col:
                        df["boll_middle"] = bbands[col]
                    elif 'BBL' in col:
                        df["boll_lower"] = bbands[col]
        except Exception as e:
            logger.warning(f"计算布林带失败: {e}")
            df["boll_upper"] = df["close"]
            df["boll_middle"] = df["close"]
            df["boll_lower"] = df["close"]

        # 获取最新一条数据
        latest = df.iloc[-1]

        indicators = TechnicalIndicators(
            symbol=symbol,
            market=market,
            date=latest.get("date", date.today()),
            ma5=float(latest.get("ma5", 0) or 0),
            ma10=float(latest.get("ma10", 0) or 0),
            ma20=float(latest.get("ma20", 0) or 0),
            ma60=float(latest.get("ma60", 0) or 0),
            macd=float(latest.get("macd", 0) or 0),
            macd_signal=float(latest.get("macd_signal", 0) or 0),
            macd_hist=float(latest.get("macd_hist", 0) or 0),
            kdj_k=float(latest.get("kdj_k", 0) or 0),
            kdj_d=float(latest.get("kdj_d", 0) or 0),
            kdj_j=float(latest.get("kdj_j", 0) or 0),
            rsi_6=float(latest.get("rsi_6", 0) or 0),
            rsi_12=float(latest.get("rsi_12", 0) or 0),
            rsi_24=float(latest.get("rsi_24", 0) or 0),
            boll_upper=float(latest.get("boll_upper", 0) or 0),
            boll_middle=float(latest.get("boll_middle", 0) or 0),
            boll_lower=float(latest.get("boll_lower", 0) or 0),
        )

        self.cache.set(cache_key, indicators)
        return indicators

    async def sync_daily(
        self,
        symbol: str,
        market: Market,
        incremental: bool = True
    ):
        """同步日线数据"""
        await self.sync_manager.sync_daily(symbol, market, incremental)

    async def sync_batch(
        self,
        symbols: list[str],
        market: Market,
        incremental: bool = True
    ):
        """批量同步日线数据"""
        await self.sync_manager.sync_batch(symbols, market, incremental)

    def get_watchlist(self) -> list[str]:
        """获取自选股列表"""
        # 从 catalog 获取
        return list(self.catalog.mapping.keys())

    def add_to_watchlist(self, symbol: str, info: dict):
        """添加到自选股"""
        self.catalog.add_instrument(symbol, info)

    def remove_from_watchlist(self, symbol: str):
        """从自选股移除"""
        self.catalog.remove_instrument(symbol)
