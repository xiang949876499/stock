"""消息推送管理器"""

from typing import Optional
from .base import BasePusher
from .wechat import WeChatPusher
from .feishu import FeishuPusher
from .telegram import TelegramPusher
from src.config import Settings
from src.infra.logger import get_logger

logger = get_logger("notification_manager")


class NotificationManager:
    """消息推送管理器"""

    def __init__(self, config: Settings):
        self.config = config
        self.pushers: dict[str, BasePusher] = {}
        self._init_pushers()

    def _init_pushers(self):
        """初始化推送器"""
        if self.config.wechat_webhook:
            self.pushers['wechat'] = WeChatPusher(self.config.wechat_webhook)

        if self.config.feishu_webhook:
            self.pushers['feishu'] = FeishuPusher(self.config.feishu_webhook)

        if self.config.telegram_bot_token and self.config.telegram_chat_id:
            self.pushers['telegram'] = TelegramPusher(
                self.config.telegram_bot_token,
                self.config.telegram_chat_id
            )

    async def push(self, content: str, channels: Optional[list[str]] = None):
        """推送消息"""
        if channels is None:
            channels = list(self.pushers.keys())

        for channel in channels:
            pusher = self.pushers.get(channel)
            if pusher:
                try:
                    success = await pusher.send(content)
                    if success:
                        logger.info(f"推送到 {channel} 成功")
                    else:
                        logger.error(f"推送到 {channel} 失败")
                except Exception as e:
                    logger.error(f"推送到 {channel} 异常: {e}")
            else:
                logger.warning(f"推送渠道 {channel} 未配置")
