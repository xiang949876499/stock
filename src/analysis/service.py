"""分析服务"""

from typing import Optional
from src.analysis.ai.base import AIModelAdapter, AnalysisResult
from src.analysis.strategies.base import AnalysisStrategy, STRATEGIES
from src.analysis.agent.stock_agent import StockAgent
from src.infra.logger import get_logger

logger = get_logger("analysis_service")


class AnalysisService:
    """分析服务"""

    def __init__(
        self,
        ai_adapter: Optional[AIModelAdapter] = None,
    ):
        self.ai_adapter = ai_adapter
        self.stock_agent = StockAgent(ai_adapter)

    async def analyze_stock(
        self,
        symbol: str,
        strategy_name: str = "comprehensive",
        context: dict = None,
    ) -> AnalysisResult:
        """分析股票

        Args:
            symbol: 股票代码
            strategy_name: 策略名称
            context: 额外上下文（如 recent_news）
        """
        return await self.stock_agent.analyze_with_strategy(symbol, strategy_name, context)

    async def chat(
        self,
        session_id: str,
        message: str
    ) -> str:
        """对话"""
        return await self.stock_agent.chat(session_id, message)

    def clear_session(self, session_id: str):
        """清除会话"""
        self.stock_agent.clear_session(session_id)
