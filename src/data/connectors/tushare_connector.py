"""Tushare 数据连接器"""

import os
from typing import Dict, Any, List

from src.data.connectors.base import DataConnector
from src.infra.logger import get_logger

logger = get_logger("tushare_connector")


class TushareConnector(DataConnector):
    """Tushare 数据连接器

    使用 Tushare Pro API 获取 A 股数据，支持日线行情、股票信息、财务指标等数据类型。
    需要设置环境变量 TUSHARE_TOKEN 或在 connect 时传入 token。
    """

    def __init__(self):
        self._token = os.getenv("TUSHARE_TOKEN", "")
        self._api = None

    @property
    def name(self) -> str:
        return "tushare"

    @property
    def capabilities(self) -> List[str]:
        return ["daily", "stock_info", "financial", "income", "balance"]

    async def connect(self, config: Dict[str, Any]) -> bool:
        """建立连接

        Args:
            config: 连接配置，可包含 "token" 字段

        Returns:
            是否连接成功
        """
        try:
            import tushare as ts
        except ImportError:
            logger.error("tushare 未安装，请执行: pip install tushare")
            return False

        self._token = config.get("token", self._token)
        if not self._token:
            logger.error("未配置 TUSHARE_TOKEN，请设置环境变量或在配置中传入 token")
            return False

        try:
            ts.set_token(self._token)
            self._api = ts.pro_api()
            logger.info("Tushare 连接成功")
            return True
        except Exception as e:
            logger.error(f"Tushare 连接失败: {e}")
            return False

    async def fetch(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """获取数据

        Args:
            query: 查询参数
                {
                    "type": "daily|stock_info|financial|income|balance",
                    "symbol": "000001.SZ",
                    "start_date": "20240101",  # daily 需要
                    "end_date": "20241231",    # daily 需要
                }

        Returns:
            数据字典
        """
        if not self._api:
            return {"error": "未连接，请先调用 connect()", "success": False}

        data_type = query.get("type", "daily")
        symbol = query.get("symbol", "")

        if not symbol:
            return {"error": "缺少股票代码", "success": False}

        fetchers = {
            "daily": self._fetch_daily,
            "stock_info": self._fetch_stock_info,
            "financial": self._fetch_financial,
            "income": self._fetch_income,
            "balance": self._fetch_balance,
        }

        fetcher = fetchers.get(data_type)
        if not fetcher:
            return {"error": f"不支持的数据类型: {data_type}", "success": False}

        try:
            return await fetcher(symbol, query)
        except Exception as e:
            logger.error(f"获取 Tushare 数据失败: {symbol}, {data_type}, {e}")
            return {"error": str(e), "success": False}

    async def disconnect(self) -> None:
        """断开连接"""
        self._api = None
        logger.info("Tushare 已断开连接")

    async def health_check(self) -> bool:
        """健康检查"""
        return self._api is not None

    async def _fetch_daily(self, symbol: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取日线数据

        Args:
            symbol: 股票代码，如 "000001.SZ"
            params: 查询参数，包含 start_date、end_date

        Returns:
            日线数据字典
        """
        start_date = params.get("start_date", "20240101")
        end_date = params.get("end_date", "20241231")

        df = self._api.daily(
            ts_code=symbol,
            start_date=start_date,
            end_date=end_date,
        )

        if df is None or df.empty:
            return {"success": True, "data": [], "message": "无数据"}

        records = df.to_dict(orient="records")
        return {"success": True, "data": records}

    async def _fetch_stock_info(self, symbol: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取股票基本信息

        Args:
            symbol: 股票代码，如 "000001.SZ"

        Returns:
            股票信息字典
        """
        df = self._api.stock_basic(
            ts_code=symbol,
            fields="ts_code,name,industry,market,list_date",
        )

        if df is None or df.empty:
            return {"success": True, "data": {}, "message": "无数据"}

        info = df.iloc[0].to_dict()
        return {"success": True, "data": info}

    async def _fetch_financial(self, symbol: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取财务指标数据

        Args:
            symbol: 股票代码，如 "000001.SZ"

        Returns:
            财务指标数据字典
        """
        df = self._api.fina_indicator(ts_code=symbol, limit=4)

        if df is None or df.empty:
            return {"success": True, "data": [], "message": "无数据"}

        records = df.to_dict(orient="records")
        return {"success": True, "data": records}

    async def _fetch_income(self, symbol: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取利润表数据

        Args:
            symbol: 股票代码，如 "000001.SZ"

        Returns:
            利润表数据字典
        """
        df = self._api.income(ts_code=symbol, limit=4)

        if df is None or df.empty:
            return {"success": True, "data": [], "message": "无数据"}

        records = df.to_dict(orient="records")
        return {"success": True, "data": records}

    async def _fetch_balance(self, symbol: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取资产负债表数据

        Args:
            symbol: 股票代码，如 "000001.SZ"

        Returns:
            资产负债表数据字典
        """
        df = self._api.balancesheet(ts_code=symbol, limit=4)

        if df is None or df.empty:
            return {"success": True, "data": [], "message": "无数据"}

        records = df.to_dict(orient="records")
        return {"success": True, "data": records}
