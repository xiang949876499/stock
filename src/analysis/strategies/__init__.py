"""分析策略"""

from .base import AnalysisStrategy, STRATEGIES
from .comprehensive import ComprehensiveStrategy
from .technical import MACrossStrategy, MACDStrategy
from .event import NewsStrategy, HotStrategy
from .fundamental import GrowthStrategy, ValueStrategy
from .trend import TrendStrategy, WaveStrategy, ChanStrategy

__all__ = [
    "AnalysisStrategy",
    "STRATEGIES",
    "ComprehensiveStrategy",
    "MACrossStrategy",
    "MACDStrategy",
    "NewsStrategy",
    "HotStrategy",
    "GrowthStrategy",
    "ValueStrategy",
    "TrendStrategy",
    "WaveStrategy",
    "ChanStrategy",
]
