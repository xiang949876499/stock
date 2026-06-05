"""分析策略测试"""

import pytest
from src.analysis.strategies.base import STRATEGIES
from src.analysis.strategies.comprehensive import ComprehensiveStrategy
from src.analysis.strategies.technical import MACrossStrategy, MACDStrategy
from src.analysis.strategies.event import NewsStrategy, HotStrategy
from src.analysis.strategies.fundamental import GrowthStrategy, ValueStrategy
from src.analysis.strategies.trend import TrendStrategy, WaveStrategy, ChanStrategy


def test_strategies_registry():
    """测试策略注册表"""
    assert "comprehensive" in STRATEGIES
    assert "ma_cross" in STRATEGIES
    assert "macd" in STRATEGIES
    assert "news" in STRATEGIES
    assert "hot" in STRATEGIES
    assert "growth" in STRATEGIES
    assert "value" in STRATEGIES
    assert "trend" in STRATEGIES
    assert "wave" in STRATEGIES
    assert "chan" in STRATEGIES


def test_comprehensive_strategy_template():
    """测试综合策略模板"""
    strategy = ComprehensiveStrategy()
    template = strategy.get_prompt_template()
    assert "{stock_name}" in template
    assert "{stock_code}" in template
    assert "{current_price}" in template
    assert "{ma5}" in template


def test_comprehensive_strategy_parse():
    """测试综合策略解析"""
    strategy = ComprehensiveStrategy()

    # 测试有效 JSON
    raw = '{"score": 85, "signal": "buy", "trend": "bullish", "reason": "看多"}'
    result = strategy.parse_result(raw)
    assert result["score"] == 85
    assert result["signal"] == "buy"

    # 测试无效 JSON
    raw = "这不是 JSON"
    result = strategy.parse_result(raw)
    assert result["score"] == 50
    assert result["signal"] == "hold"


def test_ma_cross_strategy_template():
    """测试均线金叉策略模板"""
    strategy = MACrossStrategy()
    template = strategy.get_prompt_template()
    assert "{ma5}" in template
    assert "{ma10}" in template
    assert "{ma20}" in template


def test_macd_strategy_template():
    """测试 MACD 策略模板"""
    strategy = MACDStrategy()
    template = strategy.get_prompt_template()
    assert "{macd}" in template
    assert "{macd_signal}" in template


def test_news_strategy_template():
    """测试新闻策略模板"""
    strategy = NewsStrategy()
    template = strategy.get_prompt_template()
    assert "{news}" in template


def test_growth_strategy_template():
    """测试成长策略模板"""
    strategy = GrowthStrategy()
    template = strategy.get_prompt_template()
    assert "{revenue_growth}" in template
    assert "{roe}" in template


def test_value_strategy_template():
    """测试价值策略模板"""
    strategy = ValueStrategy()
    template = strategy.get_prompt_template()
    assert "{pe}" in template
    assert "{pb}" in template


def test_trend_strategy_template():
    """测试趋势策略模板"""
    strategy = TrendStrategy()
    template = strategy.get_prompt_template()
    assert "{current_price}" in template
    assert "{ma5}" in template
