# tests/unit/test_trading_rules.py
"""交易准则测试"""

import pytest
from src.trading_rules.models import TradingRule, RuleCategory
from src.trading_rules.matcher import RuleMatcher


@pytest.fixture
def matcher():
    """匹配器实例"""
    return RuleMatcher()


def test_matcher_init(matcher):
    """测试匹配器初始化"""
    assert matcher is not None
    assert len(matcher.rules) > 0


def test_match_by_category(matcher):
    """测试按类别匹配"""
    entry_rules = matcher.match_by_category(RuleCategory.ENTRY)
    assert len(entry_rules) > 0
    assert all(r.category == RuleCategory.ENTRY for r in entry_rules)


def test_match_by_scenario(matcher):
    """测试按场景匹配"""
    buy_rules = matcher.match_by_scenario("买入")
    assert len(buy_rules) > 0


def test_match_by_tags(matcher):
    """测试按标签匹配"""
    rules = matcher.match_by_tags(["技术分析", "K线"])
    assert len(rules) > 0


def test_get_rule_by_id(matcher):
    """测试按ID获取准则"""
    rule = matcher.get_rule_by_id("RULE_001")
    assert rule is not None
    assert rule.id == "RULE_001"


def test_get_rule_by_id_not_found(matcher):
    """测试按ID获取不存在的准则"""
    rule = matcher.get_rule_by_id("RULE_999")
    assert rule is None


def test_checker_init(matcher):
    """测试检查器初始化"""
    from src.trading_rules.checker import RuleChecker
    checker = RuleChecker(matcher)
    assert checker is not None


def test_check_entry_rules(matcher):
    """测试检查买入准则"""
    from src.trading_rules.checker import RuleChecker
    checker = RuleChecker(matcher)

    stock_data = {
        "symbol": "600519",
        "current_price": 1800,
        "ma5": 1790,
        "ma10": 1780,
        "ma20": 1770,
        "ma60": 1750,
        "pe_ratio": 30,
    }

    results = checker.check_entry_rules(stock_data)
    assert len(results) > 0
    assert all(hasattr(r, 'passed') for r in results)


def test_check_exit_rules(matcher):
    """测试检查卖出准则"""
    from src.trading_rules.checker import RuleChecker
    checker = RuleChecker(matcher)

    stock_data = {
        "symbol": "600519",
        "current_price": 1800,
        "stop_loss": 1700,
    }

    results = checker.check_exit_rules(stock_data)
    assert len(results) > 0


def test_check_risk_rules(matcher):
    """测试检查风控准则"""
    from src.trading_rules.checker import RuleChecker
    checker = RuleChecker(matcher)

    portfolio = {
        "total_value": 1000000,
        "positions": [
            {"symbol": "600519", "value": 300000},
            {"symbol": "000858", "value": 200000},
        ]
    }

    results = checker.check_risk_rules(portfolio)
    assert len(results) > 0
