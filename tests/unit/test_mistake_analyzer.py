"""失误分析器测试"""

import pytest
from src.trading.mistake_analyzer import MistakeAnalyzer


@pytest.fixture
def analyzer():
    return MistakeAnalyzer()


class TestChaseHighSellLow:
    """追涨杀跌检测"""

    def test_buy_then_price_drops(self, analyzer):
        """买入后价格下跌超过2% → 追涨"""
        trades = [
            {"symbol": "600519.SSE", "side": "BUY", "price": 100.0, "created_at": "2026-06-09 09:30"},
        ]
        # 买入后价格跌到 97（跌幅 3%）
        prices = {"600519.SSE": [100.0, 99.0, 98.0, 97.0]}
        mistakes = analyzer.analyze(trades, prices)
        chase = [m for m in mistakes if m["type"] == "追涨杀跌"]
        assert len(chase) == 1
        assert chase[0]["symbol"] == "600519.SSE"
        assert "severity" in chase[0]

    def test_sell_then_price_rises(self, analyzer):
        """卖出后价格上涨超过2% → 杀跌"""
        trades = [
            {"symbol": "000858.SZE", "side": "SELL", "price": 50.0, "created_at": "2026-06-09 10:00"},
        ]
        # 卖出后价格涨到 52（涨幅 4%）
        prices = {"000858.SZE": [50.0, 50.5, 51.0, 52.0]}
        mistakes = analyzer.analyze(trades, prices)
        chase = [m for m in mistakes if m["type"] == "追涨杀跌"]
        assert len(chase) == 1
        assert chase[0]["symbol"] == "000858.SZE"

    def test_no_chase_within_threshold(self, analyzer):
        """价格变动未超过2%，不判定为追涨杀跌"""
        trades = [
            {"symbol": "600519.SSE", "side": "BUY", "price": 100.0, "created_at": "2026-06-09 09:30"},
        ]
        # 跌幅仅 1%
        prices = {"600519.SSE": [100.0, 99.5, 99.0]}
        mistakes = analyzer.analyze(trades, prices)
        chase = [m for m in mistakes if m["type"] == "追涨杀跌"]
        assert len(chase) == 0


class TestFrequentTrading:
    """频繁交易检测"""

    def test_same_symbol_more_than_two_trades(self, analyzer):
        """同股当天交易超过2次 → 频繁交易"""
        trades = [
            {"symbol": "600519.SSE", "side": "BUY", "price": 100.0, "created_at": "2026-06-09 09:30"},
            {"symbol": "600519.SSE", "side": "SELL", "price": 101.0, "created_at": "2026-06-09 10:00"},
            {"symbol": "600519.SSE", "side": "BUY", "price": 100.5, "created_at": "2026-06-09 10:30"},
        ]
        prices = {"600519.SSE": [100.0, 101.0, 100.5]}
        mistakes = analyzer.analyze(trades, prices)
        freq = [m for m in mistakes if m["type"] == "频繁交易"]
        assert len(freq) == 1
        assert freq[0]["symbol"] == "600519.SSE"

    def test_exactly_two_trades_ok(self, analyzer):
        """同股当天交易恰好2次，不判定为频繁交易"""
        trades = [
            {"symbol": "600519.SSE", "side": "BUY", "price": 100.0, "created_at": "2026-06-09 09:30"},
            {"symbol": "600519.SSE", "side": "SELL", "price": 101.0, "created_at": "2026-06-09 10:00"},
        ]
        prices = {"600519.SSE": [100.0, 101.0]}
        mistakes = analyzer.analyze(trades, prices)
        freq = [m for m in mistakes if m["type"] == "频繁交易"]
        assert len(freq) == 0


class TestLateStopLoss:
    """止损不及时检测"""

    def test_sell_with_loss_over_threshold(self, analyzer):
        """亏损超过3%才卖出 → 止损不及时"""
        trades = [
            {"symbol": "600519.SSE", "side": "BUY", "price": 100.0, "created_at": "2026-06-09 09:30"},
            {"symbol": "600519.SSE", "side": "SELL", "price": 96.0, "created_at": "2026-06-09 14:00"},
        ]
        prices = {"600519.SSE": [100.0, 98.0, 96.0]}
        mistakes = analyzer.analyze(trades, prices)
        stop_loss = [m for m in mistakes if m["type"] == "止损不及时"]
        assert len(stop_loss) == 1
        assert stop_loss[0]["symbol"] == "600519.SSE"

    def test_sell_with_loss_within_threshold(self, analyzer):
        """亏损未超过3%，不判定为止损不及时"""
        trades = [
            {"symbol": "600519.SSE", "side": "BUY", "price": 100.0, "created_at": "2026-06-09 09:30"},
            {"symbol": "600519.SSE", "side": "SELL", "price": 98.0, "created_at": "2026-06-09 14:00"},
        ]
        prices = {"600519.SSE": [100.0, 99.0, 98.0]}
        mistakes = analyzer.analyze(trades, prices)
        stop_loss = [m for m in mistakes if m["type"] == "止损不及时"]
        assert len(stop_loss) == 0


class TestNoMistakes:
    """无失误场景"""

    def test_empty_trades(self, analyzer):
        """空交易列表，无失误"""
        mistakes = analyzer.analyze([], {})
        assert mistakes == []

    def test_single_buy_no_mistake(self, analyzer):
        """单次买入且后续价格稳定，无失误"""
        trades = [
            {"symbol": "600519.SSE", "side": "BUY", "price": 100.0, "created_at": "2026-06-09 09:30"},
        ]
        prices = {"600519.SSE": [100.0, 100.5, 101.0]}
        mistakes = analyzer.analyze(trades, prices)
        assert mistakes == []
