"""Gemini 适配器"""

from typing import Optional
from .base import AIModelAdapter, AnalysisResult

from src.infra.logger import get_logger

logger = get_logger("gemini_adapter")


class GeminiAdapter(AIModelAdapter):
    """Gemini 适配器"""

    def __init__(self, api_key: str, model: str = "gemini-pro"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        """获取客户端"""
        if self._client is None:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client

    async def analyze(self, prompt: str, context: dict) -> AnalysisResult:
        """分析"""
        client = self._get_client()

        try:
            response = await client.generate_content_async(prompt)
            content = response.text

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
            logger.error(f"Gemini 分析失败: {e}")
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
            # 转换消息格式
            history = []
            for msg in messages[:-1]:
                history.append({
                    "role": msg["role"],
                    "parts": [msg["content"]]
                })

            chat = client.start_chat(history=history)
            response = await chat.send_message_async(messages[-1]["content"])
            return response.text
        except Exception as e:
            logger.error(f"Gemini 对话失败: {e}")
            return f"对话失败: {e}"
