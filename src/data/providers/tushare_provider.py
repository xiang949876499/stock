"""Tushare 数据源"""

import time
from datetime import date, datetime
from typing import Optional
import pandas as pd

from .base import DataProvider
from src.data.models import Market, StockInfo, FinancialData, NewsItem
from src.infra.logger import get_logger

logger = get_logger("tushare")

# 请求间隔控制
_last_request_time = 0
_MIN_REQUEST_INTERVAL = 0.5  # Tushare 限流较宽松


def _throttle():
    """请求节流"""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


class TushareProvider(DataProvider):
    """Tushare 数据源"""

    def __init__(self, token: str = ""):
        self.token = token
        self._pro = None

    def _get_pro(self):
        """延迟初始化 Tushare pro API"""
        if self._pro is None:
            import tushare as ts
            if not self.token:
                raise ValueError("Tushare token 未配置，请在 .env 中设置 TUSHARE_TOKEN")
            ts.set_token(self.token)
            self._pro = ts.pro_api()
        return self._pro

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
                pro = self._get_pro()

                # 转换代码格式：600519 → 600519.SH
                ts_code = self._to_ts_code(symbol, market)

                df = pro.daily(
                    ts_code=ts_code,
                    start_date=start_date.strftime("%Y%m%d"),
                    end_date=end_date.strftime("%Y%m%d"),
                )

                if df is None or df.empty:
                    raise ValueError(f"无数据: {symbol}")

                # 获取复权因子
                _throttle()
                adj_df = pro.adj_factor(
                    ts_code=ts_code,
                    start_date=start_date.strftime("%Y%m%d"),
                    end_date=end_date.strftime("%Y%m%d"),
                )

                # 重命名列
                df = df.rename(columns={
                    "trade_date": "date",
                    "vol": "volume",
                    "pct_chg": "pct_change",
                })
                df["date"] = pd.to_datetime(df["date"]).dt.date
                df["symbol"] = symbol
                df["market"] = market.value

                # 合并复权因子
                if adj_df is not None and not adj_df.empty:
                    adj_df = adj_df.rename(columns={"trade_date": "date"})
                    adj_df["date"] = pd.to_datetime(adj_df["date"]).dt.date
                    df = df.merge(adj_df[["date", "adj_factor"]], on="date", how="left")
                else:
                    df["adj_factor"] = 1.0

                df["adj_factor"] = df["adj_factor"].fillna(1.0)
                df = df.sort_values("date").reset_index(drop=True)

                return df

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
                pro = self._get_pro()
                ts_code = self._to_ts_code(symbol, market)

                df = pro.stock_basic(ts_code=ts_code, fields="ts_code,name,industry,list_date,is_delisted")

                if df is None or df.empty:
                    raise ValueError(f"未找到股票: {symbol}")

                row = df.iloc[0]
                return StockInfo(
                    symbol=symbol,
                    name=row.get("name", ""),
                    market=market,
                    industry=row.get("industry", ""),
                    list_date=self._parse_date(row.get("list_date", "")),
                    is_st=False,
                    is_active=row.get("is_delisted", "0") == "0",
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
                pro = self._get_pro()
                ts_code = self._to_ts_code(symbol, market)

                # 获取财务指标
                df = pro.fina_indicator(
                    ts_code=ts_code,
                    fields="ts_code,ann_date,eps,roe,pe,pb"
                )

                if df is None or df.empty:
                    # 尝试从 daily_basic 获取估值数据
                    _throttle()
                    basic_df = pro.daily_basic(
                        ts_code=ts_code,
                        fields="trade_date,pe_ttm,pb"
                    )
                    if basic_df is not None and not basic_df.empty:
                        latest = basic_df.iloc[0]
                        return FinancialData(
                            symbol=symbol,
                            market=market,
                            report_date=date.today(),
                            revenue=0.0,
                            net_profit=0.0,
                            eps=0.0,
                            roe=0.0,
                            pe_ratio=float(latest.get("pe_ttm", 0) or 0),
                            pb_ratio=float(latest.get("pb", 0) or 0),
                        )
                    raise ValueError(f"无财务数据: {symbol}")

                latest = df.iloc[0]
                return FinancialData(
                    symbol=symbol,
                    market=market,
                    report_date=self._parse_date(latest.get("ann_date", "")),
                    revenue=0.0,  # Tushare fina_indicator 不直接提供营收
                    net_profit=0.0,
                    eps=float(latest.get("eps", 0) or 0),
                    roe=float(latest.get("roe", 0) or 0),
                    pe_ratio=float(latest.get("pe", 0) or 0),
                    pb_ratio=float(latest.get("pb", 0) or 0),
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
                pro = self._get_pro()
                ts_code = self._to_ts_code(symbol, market)

                # Tushare 新闻接口
                df = pro.news(
                    src="sina",
                    start_date="20240101",
                    end_date=date.today().strftime("%Y%m%d"),
                )

                if df is None or df.empty:
                    return []

                # 过滤相关新闻
                if "content" in df.columns:
                    df = df[df["content"].str.contains(symbol, na=False)]

                news_list = []
                for _, row in df.head(limit).iterrows():
                    news_list.append(NewsItem(
                        id=str(row.get("id", "")),
                        symbol=symbol,
                        market=market,
                        title=str(row.get("title", "")),
                        content=str(row.get("content", "")),
                        source=str(row.get("src", "tushare")),
                        url=str(row.get("url", "")),
                        publish_time=self._parse_datetime(row.get("datetime", "")),
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

    def _to_ts_code(self, symbol: str, market: Market) -> str:
        """转换为 Tushare 代码格式：600519 → 600519.SH"""
        if market == Market.HK:
            return f"{symbol}.HK"
        # A股：6开头上海，其他深圳
        if symbol.startswith("6"):
            return f"{symbol}.SH"
        return f"{symbol}.SZ"

    def _parse_date(self, date_str: str) -> date:
        """解析日期字符串"""
        if not date_str:
            return date.today()
        try:
            return datetime.strptime(str(date_str), "%Y%m%d").date()
        except (ValueError, TypeError):
            return date.today()

    def _parse_datetime(self, dt_str: str) -> datetime:
        """解析日期时间字符串"""
        if not dt_str:
            return datetime.now()
        try:
            return datetime.strptime(str(dt_str), "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            try:
                return datetime.strptime(str(dt_str), "%Y%m%d%H%M%S")
            except (ValueError, TypeError):
                return datetime.now()
