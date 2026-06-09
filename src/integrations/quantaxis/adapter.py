"""QUANTAXIS 适配器"""

import pandas as pd
from typing import Optional

from src.integrations.base import BaseAdapter
from src.integrations.quantaxis.data_bridge import QADataBridge
from src.infra.logger import get_logger

logger = get_logger("quantaxis_adapter")


class QUANTAXISAdapter(BaseAdapter):
    """QUANTAXIS 适配器"""

    def __init__(self, enabled: bool = False):
        super().__init__(name="quantaxis", enabled=enabled)
        self.data_bridge = QADataBridge()
        self._connected = False

    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            import QUANTAXIS
            self.logger.info("QUANTAXIS 初始化成功")
            self._connected = True
            return True
        except ImportError as e:
            self.logger.warning(f"QUANTAXIS 未安装: {e}")
            return False

    async def health_check(self) -> bool:
        """健康检查"""
        return self._connected

    def list_data_types(self) -> list[str]:
        """列出支持的数据类型"""
        return ["day", "min", "tick", "l2"]

    async def fetch_market_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        data_type: str = "day",
    ) -> pd.DataFrame:
        """
        获取行情数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            data_type: 数据类型 (day/min/tick)
        """
        if not self._connected:
            self.logger.error("未连接到 QUANTAXIS")
            return pd.DataFrame()

        try:
            if data_type == "day":
                df = self.data_bridge.fetch_stock_day(symbol, start_date, end_date)
            elif data_type == "min":
                df = self.data_bridge.fetch_stock_min(symbol, start_date, end_date)
            else:
                self.logger.warning(f"不支持的数据类型: {data_type}")
                return pd.DataFrame()

            # 转换为标准格式
            df = self.data_bridge.convert_to_standard_format(df)
            self.logger.info(f"获取数据成功: {symbol}, {len(df)} 条记录")

            return df
        except Exception as e:
            self.logger.error(f"获取数据失败: {e}")
            return pd.DataFrame()
