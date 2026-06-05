"""通义千问适配器"""

from typing import Optional
from .base import AIModelAdapter, AnalysisResult

from src.infra.logger import get_logger

logger = get_logger("qwen_adapter")


class QwenAdapter(AIModelAdapter):
    """通义千问适配器"""

    def __init__(self, api_key: str, model: str = "qwen-turbo"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        """获取客户端"""
        if self._client is None:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
        return self._client

    async def analyze(self, prompt: str, context: dict) -> AnalysisResult:
        """分析"""
        client = self._get_client()

        messages = [
            {"role": "system", "content": "你是一个专业的股票分析师。"},
            {"role": "user", "content": prompt}
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
            logger.error(f"通义千问分析失败: {e}")
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
            logger.error(f"通义千问对话失败: {e}")
            return f"对话失败: {e}"
