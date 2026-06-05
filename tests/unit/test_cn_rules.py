"""国内交易规则测试"""

import pytest
from src.execution.cn_rules import CNRules


@pytest.fixture
def cn_rules():
    """国内交易规则实例"""
    return CNRules()


def test_round_to_lot(cn_rules):
    """测试取整到最小交易单位"""
    assert cn_rules.round_to_lot(150, 100) == 100
    assert cn_rules.round_to_lot(200, 100) == 200
    assert cn_rules.round_to_lot(250, 100) == 200
    assert cn_rules.round_to_lot(300, 100) == 300


def test_weight_to_volume(cn_rules):
    """测试权重转股数"""
    # 总资产 1000000，权重 0.3，股价 100，最小单位 100
    volume = cn_rules.weight_to_volume(0.3, 1000000, 100, 100)
    assert volume == 3000

    # 总资产 1000000，权重 0.5，股价 50，最小单位 100
    volume = cn_rules.weight_to_volume(0.5, 1000000, 50, 100)
    assert volume == 10000


def test_weight_to_volume_zero_price(cn_rules):
    """测试零价格"""
    volume = cn_rules.weight_to_volume(0.3, 1000000, 0, 100)
    assert volume == 0


def test_check_price_limit(cn_rules):
    """测试涨跌停检查"""
    # 正常波动
    assert cn_rules.check_price_limit("600519.SSE", 110, 100) is True

    # 超过涨跌停
    assert cn_rules.check_price_limit("600519.SSE", 120, 100) is False

    # 科创板 20%
    assert cn_rules.check_price_limit("688001.SSE", 119, 100) is True
    assert cn_rules.check_price_limit("688001.SSE", 121, 100) is False


def test_check_price_limit_zero_close(cn_rules):
    """测试零收盘价"""
    assert cn_rules.check_price_limit("600519.SSE", 100, 0) is True
