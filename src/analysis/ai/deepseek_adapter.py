"""DeepSeek 适配器"""

from typing import Optional
from .base import AIModelAdapter, AnalysisResult

from src.infra.logger import get_logger

logger = get_logger("deepseek_adapter")


class DeepSeekAdapter(AIModelAdapter):
    """DeepSeek 适配器"""

    def __init__(self, api_key: str, model: str = "deepseek-chat", base_url: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://api.deepseek.com"
        self._client = None

    def _get_client(self):
        """获取客户端"""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com"
            )
        return self._client

    async def analyze(self, prompt: str, context: dict) -> AnalysisResult:
        """分析"""
        client = self._get_client()

        # DeepSeek 要求 prompt 包含 'json' 才能使用 json_object 格式
        system_prompt = """你是一个专业的股票分析师。请以 JSON 格式输出分析结果。
输出格式：
{
    "score": 85,
    "signal": "buy",
    "trend": "bullish",
    "reason": "分析理由"
}
其中 score 为 0-100 的评分，signal 为 buy/sell/hold，trend 为 bullish/bearish/neutral。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt + "\n请以 json 格式输出结果。"}
        ]

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            import json
            result = json.loads(content)

            return AnalysisResult(
                score=result.get("score", 50),
                signal=result.get("signal", "hold"),
                trend=result.get("trend", "neutral"),
                reason=result.get("reason", ""),
                raw=content
            )
        except Exception as e:
            logger.error(f"DeepSeek 分析失败: {e}")
            return AnalysisResult(
                score=50,
                signal="hold",
                trend="neutral",
                reason=f"分析失败: {e}"
            )

    async def chat(self, messages: list[dict]) -> str:
        """多轮对话"""
        client = self._get_client()

        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"DeepSeek 对话失败: {e}")
            return f"对话失败: {e}"
