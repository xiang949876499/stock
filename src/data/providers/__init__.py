"""数据源适配器"""

from .base import DataProvider
from .akshare_provider import AkShareProvider
from .tushare_provider import TushareProvider
from .yfinance_provider import YFinanceProvider
from .ashare_skill_provider import AShareSkillProvider
from .westock_provider import WestockProvider
from .composite import CompositeProvider

__all__ = [
    "DataProvider",
    "AkShareProvider",
    "TushareProvider",
    "YFinanceProvider",
    "AShareSkillProvider",
    "WestockProvider",
    "CompositeProvider",
]
