"""WebSocket 管理器测试"""

import pytest
from src.web.websocket.manager import WebSocketManager


@pytest.fixture
def manager():
    """WebSocket 管理器实例"""
    return WebSocketManager()


def test_init(manager):
    """测试初始化"""
    assert manager.connections == {}


def test_disconnect_not_connected(manager):
    """测试断开未连接"""
    # 不应该抛出异常
    manager.disconnect("nonexistent")
