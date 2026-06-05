"""OpenAI 适配器"""

from typing import Optional
from .base import AIModelAdapter, AnalysisResult

from src.infra.logger import get_logger

logger = get_logger("openai_adapter")


class OpenAIAdapter(AIModelAdapter):
    """OpenAI 适配器"""

    def __init__(self, api_key: str, model: str = "gpt-4", base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client = None

    def _get_client(self):
        """获取客户端"""
        if self._client is None:
            from openai import AsyncOpenAI
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._client = AsyncOpenAI(**kwargs)
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
            logger.error(f"OpenAI 分析失败: {e}")
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
            logger.error(f"OpenAI 对话失败: {e}")
            return f"对话失败: {e}"
