"""Telegram 推送"""

import aiohttp
from .base import BasePusher
from src.infra.logger import get_logger

logger = get_logger("telegram_pusher")


class TelegramPusher(BasePusher):
    """Telegram 推送器"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    async def send(self, content: str) -> bool:
        """发送消息"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": self.chat_id,
                    "text": content,
                    "parse_mode": "Markdown"
                }

                async with session.post(self.api_url, json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("ok"):
                            logger.info("Telegram 推送成功")
                            return True
                        else:
                            logger.error(f"Telegram 推送失败: {result}")
                            return False
                    else:
                        logger.error(f"Telegram 推送失败: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"Telegram 推送异常: {e}")
            return False
