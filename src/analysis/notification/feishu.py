"""飞书推送"""

import aiohttp
from .base import BasePusher
from src.infra.logger import get_logger

logger = get_logger("feishu_pusher")


class FeishuPusher(BasePusher):
    """飞书推送器"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, content: str) -> bool:
        """发送消息"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "msg_type": "text",
                    "content": {
                        "text": content
                    }
                }

                async with session.post(self.webhook_url, json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("code") == 0:
                            logger.info("飞书推送成功")
                            return True
                        else:
                            logger.error(f"飞书推送失败: {result}")
                            return False
                    else:
                        logger.error(f"飞书推送失败: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"飞书推送异常: {e}")
            return False
