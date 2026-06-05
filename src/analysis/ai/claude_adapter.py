"""Claude 适配器"""

from typing import Optional
from .base import AIModelAdapter, AnalysisResult

from src.infra.logger import get_logger

logger = get_logger("claude_adapter")


class ClaudeAdapter(AIModelAdapter):
    """Claude 适配器"""

    def __init__(self, api_key: str, model: str = "claude-3-opus"):
        self.api_key = api_key
        self.model = model
        self._client = None

    def _get_client(self):
        """获取客户端"""
        if self._client is None:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def analyze(self, prompt: str, context: dict) -> AnalysisResult:
        """分析"""
        client = self._get_client()

        try:
            response = await client.messages.create(
                model=self.model,
                max_tokens=4096,
                system="你是一个专业的股票分析师。请以 JSON 格式输出分析结果。",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = response.content[0].text
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
            logger.error(f"Claude 分析失败: {e}")
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
            claude_messages = []
            system_msg = None
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    claude_messages.append(msg)

            kwargs = {
                "model": self.model,
                "max_tokens": 4096,
                "messages": claude_messages,
            }
            if system_msg:
                kwargs["system"] = system_msg

            response = await client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            logger.error(f"Claude 对话失败: {e}")
            return f"对话失败: {e}"
