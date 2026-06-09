"""统一股票数据获取器 - 支持多数据源降级"""

from typing import Dict, Any, Tuple
from datetime import datetime, timedelta

from src.infra.logger import get_logger

logger = get_logger("stock_fetcher")


def classify_stock(code: str) -> Tuple[str, str, str]:
    """识别股票市场

    Args:
        code: 股票代码，如 "600519"、"HK00700"、"TSLA"

    Returns:
        (market, normalized_code, display_code)
        market: "cn_a" | "cn_hk" | "us" | "unknown"
    """
    code = code.strip()
    upper = code.upper()

    # 港股: HK00700
    if upper.startswith("HK") and upper[2:].isdigit():
        return ("cn_hk", upper[2:], upper)

    # A股: 600519
    if upper.isdigit() and len(upper) == 6:
        return ("cn_a", upper, upper)

    # 美股: TSLA
    if upper.isalpha() and 1 <= len(upper) <= 5:
        return ("us", upper, upper)

    # 带后缀: 600519.SH / 600519.SZ / 600519.SS
    if "." in upper:
        base, suffix = upper.rsplit(".", 1)
        if suffix in ("SH", "SZ", "SS") and base.isdigit():
            return ("cn_a", base, base)

    return ("unknown", code, code)


def to_yfinance_code(code: str, market: str) -> str:
    """转换为 Yahoo Finance 代码

    Args:
        code: 标准化的股票代码
        market: 市场类型 ("cn_a" | "cn_hk" | "us")

    Returns:
        yfinance 格式代码，如 "600519.SS"、"0700.HK"、"TSLA"
    """
    if market == "cn_hk":
        num = code.lstrip("0") or "0"
        return f"{num.zfill(4)}.HK"
    if market == "us":
        return code
    # A股
    if code.startswith(("600", "601", "603", "688")):
        return f"{code}.SS"
    return f"{code}.SZ"


class StockFetcher:
    """统一股票数据获取器

    支持多市场和数据源降级策略:
    - A股: efinance > akshare > yfinance
    - 港股: efinance > akshare > yfinance
    - 美股: yfinance
    """

    def __init__(self):
        self._available_sources: Dict[str, bool] = {}

    def _check_source(self, name: str) -> bool:
        """检查数据源是否可用

        Args:
            name: 数据源模块名 (efinance / akshare / yfinance)

        Returns:
            是否可用
        """
        if name not in self._available_sources:
            try:
                __import__(name)
                self._available_sources[name] = True
            except ImportError:
                self._available_sources[name] = False
        return self._available_sources[name]

    async def fetch_daily(self, code: str, days: int = 120) -> Dict[str, Any]:
        """获取日线数据，支持降级策略

        Args:
            code: 股票代码 (如 "600519"、"HK00700"、"TSLA")
            days: 获取最近 N 天数据

        Returns:
            {"ohlcv": [...], "source": "<data_source>"}

        Raises:
            ValueError: 无法识别股票代码或所有数据源均失败
        """
        market, normalized, display = classify_stock(code)
        if market == "unknown":
            raise ValueError(f"无法识别股票代码: {code}")

        logger.info("获取日线数据", code=display, market=market, days=days)

        if market == "cn_a":
            return await self._fetch_a_share(normalized, days)
        elif market == "cn_hk":
            return await self._fetch_hk(normalized, days)
        else:
            return await self._fetch_us(normalized, days)

    # ---- A 股降级链 ----

    async def _fetch_a_share(self, code: str, days: int) -> Dict[str, Any]:
        """获取 A 股数据（降级策略: efinance > akshare > yfinance）"""
        errors = []

        # Priority 1: efinance
        if self._check_source("efinance"):
            try:
                return await self._fetch_efinance_a(code, days)
            except Exception as e:
                errors.append(f"efinance: {e}")
                logger.warning("efinance 获取 A 股失败", code=code, error=str(e))

        # Priority 2: akshare
        if self._check_source("akshare"):
            try:
                return await self._fetch_akshare_a(code, days)
            except Exception as e:
                errors.append(f"akshare: {e}")
                logger.warning("akshare 获取 A 股失败", code=code, error=str(e))

        # Priority 3: yfinance
        if self._check_source("yfinance"):
            try:
                return await self._fetch_yfinance(code, "cn_a", days)
            except Exception as e:
                errors.append(f"yfinance: {e}")
                logger.warning("yfinance 获取 A 股失败", code=code, error=str(e))

        raise ValueError(f"所有数据源失败: {'; '.join(errors)}")

    # ---- 港股降级链 ----

    async def _fetch_hk(self, code: str, days: int) -> Dict[str, Any]:
        """获取港股数据（降级策略: efinance > akshare > yfinance）"""
        errors = []

        if self._check_source("efinance"):
            try:
                return await self._fetch_efinance_hk(code, days)
            except Exception as e:
                errors.append(f"efinance: {e}")
                logger.warning("efinance 获取港股失败", code=code, error=str(e))

        if self._check_source("akshare"):
            try:
                return await self._fetch_akshare_hk(code, days)
            except Exception as e:
                errors.append(f"akshare: {e}")
                logger.warning("akshare 获取港股失败", code=code, error=str(e))

        if self._check_source("yfinance"):
            try:
                return await self._fetch_yfinance(code, "cn_hk", days)
            except Exception as e:
                errors.append(f"yfinance: {e}")
                logger.warning("yfinance 获取港股失败", code=code, error=str(e))

        raise ValueError(f"所有数据源失败: {'; '.join(errors)}")

    # ---- 美股 ----

    async def _fetch_us(self, code: str, days: int) -> Dict[str, Any]:
        """获取美股数据（仅 yfinance）"""
        if not self._check_source("yfinance"):
            raise ValueError("yfinance 未安装，无法获取美股数据")
        return await self._fetch_yfinance(code, "us", days)

    # ---- efinance 数据源 ----

    async def _fetch_efinance_a(self, code: str, days: int) -> Dict[str, Any]:
        """通过 efinance 获取 A 股"""
        import efinance as ef
        df = ef.stock.get_quote_history(code)
        return self._normalize_dataframe(df, "efinance")

    async def _fetch_efinance_hk(self, code: str, days: int) -> Dict[str, Any]:
        """通过 efinance 获取港股"""
        import efinance as ef
        df = ef.stock.get_quote_history(code, stock_type="hk")
        return self._normalize_dataframe(df, "efinance")

    # ---- akshare 数据源 ----

    async def _fetch_akshare_a(self, code: str, days: int) -> Dict[str, Any]:
        """通过 akshare 获取 A 股"""
        import akshare as ak
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
        return self._normalize_dataframe(df, "akshare")

    async def _fetch_akshare_hk(self, code: str, days: int) -> Dict[str, Any]:
        """通过 akshare 获取港股"""
        import akshare as ak
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days * 2)).strftime("%Y%m%d")
        df = ak.stock_hk_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
        return self._normalize_dataframe(df, "akshare")

    # ---- yfinance 数据源 ----

    async def _fetch_yfinance(self, code: str, market: str, days: int) -> Dict[str, Any]:
        """通过 yfinance 获取数据"""
        import yfinance as yf
        yf_code = to_yfinance_code(code, market)
        ticker = yf.Ticker(yf_code)
        hist = ticker.history(period=f"{days}d")

        ohlcv = []
        for idx, row in hist.iterrows():
            date_str = idx.strftime("%Y-%m-%d")
            ohlcv.append({
                "date": date_str,
                "open": float(row.get("Open", 0)),
                "high": float(row.get("High", 0)),
                "low": float(row.get("Low", 0)),
                "close": float(row.get("Close", 0)),
                "volume": float(row.get("Volume", 0)),
            })

        return {"ohlcv": ohlcv, "source": "yfinance"}

    # ---- 标准化 ----

    def _normalize_dataframe(self, df, source: str) -> Dict[str, Any]:
        """标准化 DataFrame 格式为统一 OHLCV 结构

        Args:
            df: pandas DataFrame
            source: 数据源名称 ("efinance" | "akshare")

        Returns:
            {"ohlcv": [...], "source": "<source>"}
        """
        col_maps = {
            "efinance": {
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
            },
            "akshare": {
                "日期": "date",
                "开盘": "open",
                "收盘": "close",
                "最高": "high",
                "最低": "low",
                "成交量": "volume",
            },
        }

        col_map = col_maps.get(source, {})
        df = df.rename(columns=col_map)

        ohlcv = []
        for _, row in df.iterrows():
            ohlcv.append({
                "date": str(row.get("date", "")),
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": float(row.get("volume", 0)),
            })

        return {"ohlcv": ohlcv, "source": source}
