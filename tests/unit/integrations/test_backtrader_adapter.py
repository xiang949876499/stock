import pytest
from unittest.mock import Mock, patch
from src.integrations.backtrader.adapter import BacktraderAdapter


@pytest.fixture
def adapter():
    return BacktraderAdapter()


def test_adapter_creation(adapter):
    """测试适配器创建"""
    assert adapter.name == "backtrader"
    assert adapter.is_available() is True


def test_adapter_list_strategies(adapter):
    """测试列出策略"""
    strategies = adapter.list_strategies()
    assert "ma_cross" in strategies
    assert "macd" in strategies


@pytest.mark.asyncio
async def test_adapter_health_check(adapter):
    """测试健康检查"""
    result = await adapter.health_check()
    assert result is True
