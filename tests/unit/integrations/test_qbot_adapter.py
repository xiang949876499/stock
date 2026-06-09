import pytest
from src.integrations.qbot.adapter import QbotAdapter


def test_adapter_creation():
    """测试适配器创建"""
    adapter = QbotAdapter(enabled=False)
    assert adapter.name == "qbot"


def test_list_algorithms():
    """测试列出算法"""
    adapter = QbotAdapter(enabled=False)
    algorithms = adapter.list_algorithms()
    assert "dqn" in algorithms
    assert "ppo" in algorithms
