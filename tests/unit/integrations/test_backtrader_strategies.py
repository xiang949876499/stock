import pytest
from src.integrations.backtrader.strategies import (
    MACrossStrategy,
    MACDStrategy,
    RSIStrategy,
    BollingerStrategy,
    get_strategy_class,
    list_strategies,
)


def test_list_strategies():
    """测试列出策略"""
    strategies = list_strategies()
    assert "ma_cross" in strategies
    assert "macd" in strategies
    assert "rsi" in strategies
    assert "bollinger" in strategies


def test_get_strategy_class():
    """测试获取策略类"""
    cls = get_strategy_class("ma_cross")
    assert cls is MACrossStrategy


def test_get_strategy_class_not_found():
    """测试获取不存在的策略"""
    cls = get_strategy_class("not_exist")
    assert cls is None
