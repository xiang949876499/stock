"""股票问答 Agent"""

from typing import Optional
from src.analysis.ai.base import AIModelAdapter, AnalysisResult
from src.analysis.strategies.base import AnalysisStrategy, STRATEGIES
from src.analysis.agent.session import ChatSession
from src.infra.logger import get_logger

logger = get_logger("stock_agent")


class StockAgent:
    """股票问答 Agent"""

    def __init__(
        self,
        ai_adapter: Optional[AIModelAdapter] = None,
    ):
        self.ai_adapter = ai_adapter
        self.sessions: dict[str, ChatSession] = {}

    async def chat(
        self,
        session_id: str,
        user_message: str
    ) -> str:
        """多轮对话"""
        # 获取或创建会话
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(session_id)

        session = self.sessions[session_id]

        # 添加用户消息
        session.add_message("user", user_message)

        # AI 回复
        if self.ai_adapter:
            messages = session.get_messages()
            response = await self.ai_adapter.chat(messages)
        else:
            response = "AI 适配器未配置，请在设置中配置 API Key。"

        # 添加 AI 回复
        session.add_message("assistant", response)

        return response

    async def analyze_with_strategy(
        self,
        stock_code: str,
        strategy_name: str = "comprehensive",
        context: dict = None,
    ) -> AnalysisResult:
        """使用策略分析股票"""
        strategy = STRATEGIES.get(strategy_name)
        if not strategy:
            raise ValueError(f"策略 {strategy_name} 不存在")

        # 构建上下文
        if context is None:
            context = {}

        # 尝试获取实际数据
        try:
            from src.data.service import DataService
            from src.data.models import Market

            data_service = DataService()

            # 获取股票信息
            catalog_info = data_service.catalog.mapping.get(stock_code, {})
            stock_name = catalog_info.get("name", stock_code)

            # 获取技术指标
            try:
                indicators = await data_service.get_technical_indicators(stock_code, Market.A)
                context.update({
                    "stock_name": stock_name,
                    "stock_code": stock_code,
                    "current_price": 0,  # 需要从行情获取
                    "ma5": indicators.ma5,
                    "ma10": indicators.ma10,
                    "ma20": indicators.ma20,
                    "ma60": indicators.ma60,
                    "macd": indicators.macd,
                    "macd_signal": indicators.macd_signal,
                    "macd_hist": indicators.macd_hist,
                    "rsi_6": indicators.rsi_6,
                    "rsi_12": indicators.rsi_12,
                    "rsi_24": indicators.rsi_24,
                    "kdj_k": indicators.kdj_k,
                    "kdj_d": indicators.kdj_d,
                    "kdj_j": indicators.kdj_j,
                })
            except Exception as e:
                logger.warning(f"获取技术指标失败: {e}")
                context.setdefault("stock_name", stock_name)
                context.setdefault("stock_code", stock_code)

        except Exception as e:
            logger.warning(f"获取股票数据失败: {e}")
            context.setdefault("stock_name", stock_code)
            context.setdefault("stock_code", stock_code)

        # 填充默认值
        default_context = {
            "stock_name": context.get("stock_name", stock_code),
            "stock_code": stock_code,
            "current_price": context.get("current_price", 0),
            "ma5": context.get("ma5", 0),
            "ma10": context.get("ma10", 0),
            "ma20": context.get("ma20", 0),
            "ma60": context.get("ma60", 0),
            "macd": context.get("macd", 0),
            "macd_signal": context.get("macd_signal", 0),
            "macd_hist": context.get("macd_hist", 0),
            "rsi_6": context.get("rsi_6", 0),
            "rsi_12": context.get("rsi_12", 0),
            "rsi_24": context.get("rsi_24", 0),
            "kdj_k": context.get("kdj_k", 0),
            "kdj_d": context.get("kdj_d", 0),
            "kdj_j": context.get("kdj_j", 0),
        }

        # 获取提示词
        try:
            prompt = strategy.get_prompt_template().format(**default_context)
        except KeyError as e:
            logger.warning(f"提示词模板缺少参数: {e}")
            prompt = strategy.get_prompt_template()

        # AI 分析
        if self.ai_adapter:
            result = await self.ai_adapter.analyze(prompt, default_context)
        else:
            result = AnalysisResult(
                score=50,
                signal="hold",
                trend="neutral",
                reason="AI 适配器未配置"
            )

        return result

    def clear_session(self, session_id: str):
        """清除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"清除会话: {session_id}")

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取会话"""
        return self.sessions.get(session_id)

    def list_sessions(self) -> list[str]:
        """列出所有会话"""
        return list(self.sessions.keys())
