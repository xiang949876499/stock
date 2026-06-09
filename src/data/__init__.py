"""数据层"""

from .models import Market, StockDaily, StockInfo, FinancialData, NewsItem, TechnicalIndicators
from .providers.base import DataProvider
from .providers.akshare_provider import AkShareProvider
from .catalog.manager import InstrumentCatalog
from .storage.parquet import ParquetStorage
from .service import DataService
from .connectors import DataConnector, ConnectorRegistry, HKStockConnector

__all__ = [
    "Market",
    "StockDaily",
    "StockInfo",
    "FinancialData",
    "NewsItem",
    "TechnicalIndicators",
    "DataProvider",
    "AkShareProvider",
    "InstrumentCatalog",
    "ParquetStorage",
    "DataService",
    "DataConnector",
    "ConnectorRegistry",
    "HKStockConnector",
]
