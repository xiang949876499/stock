"""分析策略基类"""

from abc import ABC, abstractmethod


class AnalysisStrategy(ABC):
    """分析策略基类"""

    @abstractmethod
    def get_prompt_template(self) -> str:
        """获取提示词模板"""
        pass

    @abstractmethod
    def parse_result(self, raw: str) -> dict:
        """解析结果"""
        pass


# 内置策略
from .comprehensive import ComprehensiveStrategy
from .technical import MACrossStrategy, MACDStrategy
from .event import NewsStrategy, HotStrategy
from .fundamental import GrowthStrategy, ValueStrategy
from .trend import TrendStrategy, WaveStrategy, ChanStrategy


# 策略注册表
STRATEGIES = {
    "comprehensive": ComprehensiveStrategy(),
    "ma_cross": MACrossStrategy(),
    "macd": MACDStrategy(),
    "news": NewsStrategy(),
    "hot": HotStrategy(),
    "growth": GrowthStrategy(),
    "value": ValueStrategy(),
    "trend": TrendStrategy(),
    "wave": WaveStrategy(),
    "chan": ChanStrategy(),
}
