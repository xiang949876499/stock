import pytest
from src.integrations.ai_quant.adapter import AIQuantAdapter


def test_adapter_creation():
    """测试适配器创建"""
    adapter = AIQuantAdapter()
    assert adapter.name == "ai_quant"


def test_list_strategies():
    """测试列出策略"""
    adapter = AIQuantAdapter()
    strategies = adapter.list_strategies()
    assert "xgboost" in strategies
    assert "random_forest" in strategies
