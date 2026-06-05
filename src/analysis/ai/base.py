"""AI 模型适配器基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AnalysisResult:
    """分析结果"""
    score: float
    signal: str  # buy/sell/hold
    trend: str  # bullish/bearish/neutral
    reason: str
    raw: str = ""


class AIModelAdapter(ABC):
    """AI 模型适配器基类"""

    @abstractmethod
    async def analyze(
        self,
        prompt: str,
        context: dict
    ) -> AnalysisResult:
        """分析"""
        pass

    @abstractmethod
    async def chat(
        self,
        messages: list[dict]
    ) -> str:
        """多轮对话"""
        pass
