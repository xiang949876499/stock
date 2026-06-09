"""数据连接器模块"""

from .base import DataConnector
from .registry import ConnectorRegistry
from .hk_stock_connector import HKStockConnector
from .tushare_connector import TushareConnector

# 注册内置连接器
ConnectorRegistry.register(HKStockConnector())
ConnectorRegistry.register(TushareConnector())

__all__ = ["DataConnector", "ConnectorRegistry", "HKStockConnector", "TushareConnector"]
