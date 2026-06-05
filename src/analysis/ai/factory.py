"""AI 模型工厂"""

from typing import Optional
from .base import AIModelAdapter
from .openai_adapter import OpenAIAdapter
from .claude_adapter import ClaudeAdapter
from .deepseek_adapter import DeepSeekAdapter
from .qwen_adapter import QwenAdapter
from .gemini_adapter import GeminiAdapter
from src.config import Settings
from src.infra.logger import get_logger

logger = get_logger("ai_factory")


class AIModelFactory:
    """AI 模型工厂"""

    @staticmethod
    def create(config: Settings) -> Optional[AIModelAdapter]:
        """创建 AI 模型适配器"""
        if not config.ai_api_key:
            logger.warning("AI API Key 未配置")
            return None

        adapters = {
            'openai': OpenAIAdapter,
            'claude': ClaudeAdapter,
            'deepseek': DeepSeekAdapter,
            'qwen': QwenAdapter,
            'gemini': GeminiAdapter,
        }

        adapter_class = adapters.get(config.ai_provider)
        if not adapter_class:
            logger.error(f"不支持的 AI 提供商: {config.ai_provider}")
            return None

        kwargs = {
            "api_key": config.ai_api_key,
            "model": config.ai_model,
        }
        if config.ai_base_url:
            kwargs["base_url"] = config.ai_base_url

        return adapter_class(**kwargs)
