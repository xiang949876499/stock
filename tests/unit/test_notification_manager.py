"""消息推送管理器测试"""

import pytest
from src.analysis.notification.manager import NotificationManager
from src.analysis.notification.wechat import WeChatPusher
from src.analysis.notification.feishu import FeishuPusher
from src.analysis.notification.telegram import TelegramPusher
from src.config import Settings


def test_notification_manager_init():
    """测试消息推送管理器初始化"""
    config = Settings(
        wechat_webhook="https://example.com/wechat",
        feishu_webhook="https://example.com/feishu",
        telegram_bot_token="test_token",
        telegram_chat_id="test_chat_id",
    )
    manager = NotificationManager(config)
    assert "wechat" in manager.pushers
    assert "feishu" in manager.pushers
    assert "telegram" in manager.pushers


def test_notification_manager_init_empty():
    """测试空配置的消息推送管理器"""
    config = Settings()
    manager = NotificationManager(config)
    assert len(manager.pushers) == 0


def test_wechat_pusher_init():
    """测试企业微信推送器初始化"""
    pusher = WeChatPusher("https://example.com/wechat")
    assert pusher.webhook_url == "https://example.com/wechat"


def test_feishu_pusher_init():
    """测试飞书推送器初始化"""
    pusher = FeishuPusher("https://example.com/feishu")
    assert pusher.webhook_url == "https://example.com/feishu"


def test_telegram_pusher_init():
    """测试 Telegram 推送器初始化"""
    pusher = TelegramPusher("test_token", "test_chat_id")
    assert pusher.bot_token == "test_token"
    assert pusher.chat_id == "test_chat_id"
    assert "test_token" in pusher.api_url
