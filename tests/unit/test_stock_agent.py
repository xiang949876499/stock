"""股票 Agent 测试"""

import pytest
import asyncio
from src.analysis.agent.stock_agent import StockAgent
from src.analysis.agent.session import ChatSession, Message


@pytest.fixture
def agent():
    """Agent 实例"""
    return StockAgent()


def test_agent_init(agent):
    """测试 Agent 初始化"""
    assert agent.ai_adapter is None
    assert len(agent.sessions) == 0


def test_agent_list_sessions(agent):
    """测试列出会话"""
    sessions = agent.list_sessions()
    assert len(sessions) == 0


def test_agent_clear_session(agent):
    """测试清除会话"""
    agent.clear_session("nonexistent")
    # 不应该抛出异常


def test_agent_get_session(agent):
    """测试获取会话"""
    session = agent.get_session("test")
    assert session is None


def test_chat_session_init():
    """测试会话初始化"""
    session = ChatSession("test")
    assert session.session_id == "test"
    assert len(session.messages) == 0


def test_chat_session_add_message():
    """测试添加消息"""
    session = ChatSession("test")
    session.add_message("user", "你好")
    assert len(session.messages) == 1
    assert session.messages[0].role == "user"
    assert session.messages[0].content == "你好"


def test_chat_session_get_messages():
    """测试获取消息"""
    session = ChatSession("test")
    session.add_message("user", "你好")
    session.add_message("assistant", "你好！")

    messages = session.get_messages()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "你好"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "你好！"


def test_chat_session_clear():
    """测试清空会话"""
    session = ChatSession("test")
    session.add_message("user", "你好")
    session.clear()
    assert len(session.messages) == 0


def test_message_init():
    """测试消息初始化"""
    message = Message(role="user", content="你好")
    assert message.role == "user"
    assert message.content == "你好"
    assert message.timestamp is not None
