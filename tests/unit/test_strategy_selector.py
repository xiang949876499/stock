"""StrategySelector 动态策略选择器测试"""

import math
import pytest

from src.trading.strategy_selector import StrategySelector


@pytest.fixture
def selector():
    return StrategySelector()


# ── _get_market_state ──────────────────────────────────────────────

class TestGetMarketState:
    """_get_market_state 测试"""

    def test_insufficient_data_returns_default(self, selector: StrategySelector):
        """不足 20 条数据 → default"""
        closes = [100.0] * 19
        assert selector._get_market_state(closes) == "default"

    def test_empty_data_returns_default(self, selector: StrategySelector):
        """空列表 → default"""
        assert selector._get_market_state([]) == "default"

    def test_trending_up(self, selector: StrategySelector):
        """20 日涨幅 > 5% → trending"""
        # 构造连续上涨: 从 100 涨到 110 (涨幅 10%)
        closes = [100.0 + i * (10.0 / 19) for i in range(20)]
        assert selector._get_market_state(closes) == "trending"

    def test_trending_down_oversold(self, selector: StrategySelector):
        """20 日跌幅 > 5% → oversold"""
        # 构造连续下跌: 从 110 跌到 100 (跌幅 ~9%)
        closes = [110.0 - i * (10.0 / 19) for i in range(20)]
        assert selector._get_market_state(closes) == "oversold"

    def test_volatile(self, selector: StrategySelector):
        """高波动率 (标准差 > 0.02 的日收益率) → volatile"""
        # 构造大幅震荡行情: 涨跌幅不大但波动剧烈
        # 日收益率在 [-0.05, +0.05] 之间大幅摆动, 标准差 > 0.02
        base = 100.0
        fluctuation = [
            0.05, -0.05, 0.05, -0.05, 0.05,
            -0.05, 0.05, -0.05, 0.05, -0.05,
            0.05, -0.05, 0.05, -0.05, 0.05,
            -0.05, 0.05, -0.05, 0.05, 0.0,
        ]
        closes = [base]
        for r in fluctuation[1:]:
            closes.append(closes[-1] * (1 + r))
        # 确保总涨幅在 ±5% 以内, 但波动率够高
        state = selector._get_market_state(closes)
        assert state == "volatile"

    def test_default_stable(self, selector: StrategySelector):
        """平稳行情 (低波动、低涨跌) → default"""
        # 构造稳定行情: 几乎无波动
        closes = [100.0 + 0.01 * i for i in range(20)]
        assert selector._get_market_state(closes) == "default"

    def test_exactly_20_days_border(self, selector: StrategySelector):
        """恰好 20 条数据应正常判断, 而非返回 default"""
        closes = [100.0] * 20
        # 涨跌幅 0, 波动率 0 → default
        assert selector._get_market_state(closes) == "default"


# ── select ─────────────────────────────────────────────────────────

class TestSelect:
    """select 测试"""

    def test_select_trending(self, selector: StrategySelector):
        """趋势行情 → trend"""
        closes = [100.0 + i * (10.0 / 19) for i in range(20)]
        assert selector.select(closes) == "trend"

    def test_select_volatile(self, selector: StrategySelector):
        """震荡行情 → macd"""
        fluctuation = [
            0.05, -0.05, 0.05, -0.05, 0.05,
            -0.05, 0.05, -0.05, 0.05, -0.05,
            0.05, -0.05, 0.05, -0.05, 0.05,
            -0.05, 0.05, -0.05, 0.05, 0.0,
        ]
        closes = [100.0]
        for r in fluctuation[1:]:
            closes.append(closes[-1] * (1 + r))
        assert selector.select(closes) == "macd"

    def test_select_oversold(self, selector: StrategySelector):
        """超卖反弹 → ma_cross"""
        closes = [110.0 - i * (10.0 / 19) for i in range(20)]
        assert selector.select(closes) == "ma_cross"

    def test_select_default(self, selector: StrategySelector):
        """默认 → comprehensive"""
        closes = [100.0] * 20
        assert selector.select(closes) == "comprehensive"

    def test_select_insufficient_data(self, selector: StrategySelector):
        """数据不足 → comprehensive"""
        assert selector.select([100.0]) == "comprehensive"


# ── STRATEGIES mapping ─────────────────────────────────────────────

class TestStrategiesMapping:
    """STRATEGIES 映射正确性"""

    def test_all_keys_present(self):
        assert set(StrategySelector.STRATEGIES.keys()) == {
            "trending", "volatile", "oversold", "default",
        }

    def test_all_values_are_valid_strategies(self):
        valid = {"trend", "macd", "ma_cross", "comprehensive"}
        assert set(StrategySelector.STRATEGIES.values()) == valid

    def test_trending_maps_to_trend(self):
        assert StrategySelector.STRATEGIES["trending"] == "trend"

    def test_volatile_maps_to_macd(self):
        assert StrategySelector.STRATEGIES["volatile"] == "macd"

    def test_oversold_maps_to_ma_cross(self):
        assert StrategySelector.STRATEGIES["oversold"] == "ma_cross"

    def test_default_maps_to_comprehensive(self):
        assert StrategySelector.STRATEGIES["default"] == "comprehensive"
