"""企业微信推送"""

import aiohttp
from .base import BasePusher
from src.infra.logger import get_logger

logger = get_logger("wechat_pusher")


class WeChatPusher(BasePusher):
    """企业微信推送器"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send(self, content: str) -> bool:
        """发送消息"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "msgtype": "markdown",
                    "markdown": {
                        "content": content
                    }
                }

                async with session.post(self.webhook_url, json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        if result.get("errcode") == 0:
                            logger.info("企业微信推送成功")
                            return True
                        else:
                            logger.error(f"企业微信推送失败: {result}")
                            return False
                    else:
                        logger.error(f"企业微信推送失败: {resp.status}")
                        return False
        except Exception as e:
            logger.error(f"企业微信推送异常: {e}")
            return False
