"""AkShare 数据源"""

import time
from datetime import date, datetime
from typing import Optional
import os
import pandas as pd

# 清除所有代理环境变量（防止 requests 读取 Windows 系统代理）
for _key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(_key, None)
os.environ['NO_PROXY'] = '*'

import akshare as ak
import requests as _requests

# 强制 requests 不使用任何代理（绕过 Clash/V2Ray 等系统代理）+ 连接超时
_original_request = _requests.Session.request
def _no_proxy_request(self, method, url, **kwargs):
    kwargs['proxies'] = {'http': None, 'https': None}
    # 设置连接超时，防止长时间挂起
    if 'timeout' not in kwargs or kwargs['timeout'] is None:
        kwargs['timeout'] = (5, 15)  # connect=5s, read=15s
    return _original_request(self, method, url, **kwargs)
_requests.Session.request = _no_proxy_request

from .base import DataProvider
from src.data.models import Market, StockInfo, FinancialData, NewsItem
from src.infra.logger import get_logger

logger = get_logger("akshare")

# 请求间隔控制（防止限流）
_last_request_time = 0
_MIN_REQUEST_INTERVAL = 1.5  # 最小间隔 1.5s，防止被限流


def _throttle():
    """请求节流，防止被限流"""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()


class AkShareProvider(DataProvider):
    """AkShare 数据源（带重试和节流）"""

    async def fetch_daily(
        self,
        symbol: str,
        market: Market,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """获取日线数据（快速失败，让 CompositeProvider 处理 fallback）"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                _throttle()
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
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 2  # 2s, 4s
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
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if market == Market.A:
                    # 获取 A 股财务指标
                    _throttle()
                    df = ak.stock_financial_analysis_indicator(symbol=symbol)

                    if df is None or df.empty:
                        raise ValueError(f"无财务数据: {symbol}")

                    latest = df.iloc[0]
                    return FinancialData(
                        symbol=symbol,
                        market=market,
                        report_date=self._parse_date(latest.get("日期", "")),
                        revenue=float(latest.get("主营业务收入(万元)", 0) or 0) * 10000,
                        net_profit=float(latest.get("净利润(万元)", 0) or 0) * 10000,
                        eps=float(latest.get("每股收益(元)", 0) or 0),
                        roe=float(latest.get("净资产收益率(%)", 0) or 0),
                        pe_ratio=0.0,  # 需要从行情接口获取
                        pb_ratio=0.0,
                    )
                elif market == Market.HK:
                    # 港股财务数据：使用 stock_a_indicator_lg 获取估值
                    raise ValueError(f"港股财务数据暂不支持: {market}")
                else:
                    raise ValueError(f"不支持的市场: {market}")

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
                if market == Market.A:
                    _throttle()
                    # 使用东方财富新闻接口
                    df = ak.stock_news_em(symbol=symbol)

                    if df is None or df.empty:
                        return []

                    news_list = []
                    for _, row in df.head(limit).iterrows():
                        news_list.append(NewsItem(
                            id=str(row.get("新闻ID", row.name)),
                            symbol=symbol,
                            market=market,
                            title=str(row.get("新闻标题", "")),
                            content=str(row.get("新闻内容", "")),
                            source=str(row.get("文章来源", "")),
                            url=str(row.get("新闻链接", "")),
                            publish_time=self._parse_datetime(row.get("发布时间", "")),
                            sentiment="neutral",
                            importance="P2",
                        ))

                    return news_list
                else:
                    # 非 A 股暂不支持新闻
                    logger.warning(f"暂不支持 {market} 市场新闻: {symbol}")
                    return []

            except Exception as e:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 3
                    logger.warning(f"获取新闻失败，{wait}秒后重试 ({attempt+1}/{max_retries}): {symbol}, {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"获取新闻失败: {symbol}, {market}, {e}")
                    return []

    def _parse_date(self, date_str) -> date:
        """解析日期"""
        if not date_str:
            return date.today()
        try:
            if isinstance(date_str, str):
                for fmt in ["%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"]:
                    try:
                        return datetime.strptime(date_str, fmt).date()
                    except ValueError:
                        continue
            return date.today()
        except Exception:
            return date.today()

    def _parse_datetime(self, dt_str) -> datetime:
        """解析日期时间"""
        if not dt_str:
            return datetime.now()
        try:
            if isinstance(dt_str, str):
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y%m%d%H%M%S"]:
                    try:
                        return datetime.strptime(dt_str, fmt)
                    except ValueError:
                        continue
            return datetime.now()
        except Exception:
            return datetime.now()

    async def fetch_stock_list_a(self) -> list[dict]:
        """获取全部 A 股列表（代码+名称）

        Returns:
            [{"symbol": "600519", "name": "贵州茅台", "market": "A"}, ...]
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                _throttle()
                df = ak.stock_info_a_code_name()
                if df is None or df.empty:
                    logger.warning("获取 A 股列表为空")
                    return []

                stocks = []
                for _, row in df.iterrows():
                    code = str(row["code"]).zfill(6)
                    name = row["name"]
                    # 跳过 ST、退市、B 股
                    if "ST" in name or "退" in name or code.startswith("9"):
                        continue
                    stocks.append({
                        "symbol": code,
                        "name": name,
                        "market": "A",
                    })

                logger.info(f"获取 A 股列表: {len(stocks)} 只")
                return stocks

            except Exception as e:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 3
                    logger.warning(f"获取 A 股列表失败，{wait}秒后重试 ({attempt+1}/{max_retries}): {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"获取 A 股列表失败: {e}")
                    return []

    async def fetch_stock_list_hk(self) -> list[dict]:
        """获取全部港股主板列表

        Returns:
            [{"symbol": "00700", "name": "腾讯控股", "market": "HK"}, ...]
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                _throttle()
                df = ak.stock_hk_main_board_spot_em()
                if df is None or df.empty:
                    logger.warning("获取港股列表为空")
                    return []

                stocks = []
                for _, row in df.iterrows():
                    code = str(row.get("代码", "")).zfill(5)
                    name = row.get("名称", "")
                    if not code or not name:
                        continue
                    stocks.append({
                        "symbol": code,
                        "name": name,
                        "market": "HK",
                    })

                logger.info(f"获取港股列表: {len(stocks)} 只")
                return stocks

            except Exception as e:
                if attempt < max_retries - 1:
                    wait = (attempt + 1) * 3
                    logger.warning(f"获取港股列表失败，{wait}秒后重试 ({attempt+1}/{max_retries}): {e}")
                    time.sleep(wait)
                else:
                    logger.error(f"获取港股列表失败: {e}")
                    return []
