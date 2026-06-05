"""信号桥接器测试"""

import pytest
import asyncio
from src.execution.bridge.signal_bridge import SignalBridge, OrderPlan
from src.execution.risk.risk_manager import RiskManager
from src.execution.cn_rules import CNRules
from src.data.catalog.manager import InstrumentCatalog
from src.research.signals.generator import Signal, SignalStatus, SignalSource


@pytest.fixture
def signal_bridge():
    """信号桥接器实例"""
    return SignalBridge(
        risk_manager=RiskManager(),
        catalog=InstrumentCatalog(),
        cn_rules=CNRules(),
    )


@pytest.fixture
def published_signal():
    """已发布信号"""
    return Signal(
        signal_id="test-001",
        as_of="2026-01-01T00:00:00",
        source=SignalSource.MANUAL,
        status=SignalStatus.PUBLISHED,
        targets={
            "600519.SSE": 0.3,
            "000858.SZE": 0.2,
        },
    )


@pytest.fixture
def draft_signal():
    """草稿信号"""
    return Signal(
        signal_id="test-002",
        as_of="2026-01-01T00:00:00",
        source=SignalSource.MANUAL,
        status=SignalStatus.DRAFT,
        targets={
            "600519.SSE": 0.3,
        },
    )


@pytest.mark.asyncio
async def test_process_published_signal(signal_bridge, published_signal):
    """测试处理已发布信号"""
    orders = await signal_bridge.process_signal(published_signal)
    assert len(orders) == 2
    assert orders[0].vt_symbol == "600519.SSE"
    assert orders[0].side == "BUY"


@pytest.mark.asyncio
async def test_process_draft_signal(signal_bridge, draft_signal):
    """测试处理草稿信号"""
    orders = await signal_bridge.process_signal(draft_signal)
    assert len(orders) == 0


@pytest.mark.asyncio
async def test_process_signal_with_positions(signal_bridge, published_signal):
    """测试带持仓的信号处理"""
    current_positions = {
        "600519.SSE": 0.2,
        "000858.SZE": 0.3,
    }
    orders = await signal_bridge.process_signal(published_signal, current_positions)
    # 600519: 0.3 - 0.2 = 0.1 > 0.01, BUY
    # 000858: 0.2 - 0.3 = -0.1 < -0.01, SELL
    assert len(orders) == 2

    buy_order = next(o for o in orders if o.vt_symbol == "600519.SSE")
    sell_order = next(o for o in orders if o.vt_symbol == "000858.SZE")

    assert buy_order.side == "BUY"
    assert sell_order.side == "SELL"


def test_calculate_volume(signal_bridge):
    """测试计算订单数量"""
    order = OrderPlan(
        vt_symbol="600519.SSE",
        side="BUY",
        target_weight=0.3,
        current_weight=0.0,
    )
    volume = signal_bridge.calculate_volume(
        order=order,
        total_equity=1000000,
        last_price=1800.0,
        lot_size=100,
    )
    # 1000000 * 0.3 / 1800 = 166.67 -> 100
    assert volume == 100


def test_validate_order_valid(signal_bridge):
    """测试验证有效订单"""
    order = OrderPlan(
        vt_symbol="600519.SSE",
        side="BUY",
        target_weight=0.3,
        current_weight=0.0,
        volume=100,
    )
    is_valid, reason = signal_bridge.validate_order(order, 1800.0, 1800.0)
    assert is_valid is True


def test_validate_order_price_limit(signal_bridge):
    """测试验证涨跌停订单"""
    order = OrderPlan(
        vt_symbol="600519.SSE",
        side="BUY",
        target_weight=0.3,
        current_weight=0.0,
        volume=100,
    )
    # 价格超过涨跌停
    is_valid, reason = signal_bridge.validate_order(order, 2000.0, 1800.0)
    assert is_valid is False
    assert "涨跌停" in reason


def test_generate_execution_plan(signal_bridge):
    """测试生成执行计划"""
    orders = [
        OrderPlan(
            vt_symbol="600519.SSE",
            side="BUY",
            target_weight=0.3,
            current_weight=0.0,
        ),
        OrderPlan(
            vt_symbol="000858.SZE",
            side="SELL",
            target_weight=0.0,
            current_weight=0.2,
        ),
    ]

    prices = {
        "600519.SSE": 1800.0,
        "000858.SZE": 150.0,
    }

    plan = signal_bridge.generate_execution_plan(orders, 1000000, prices)
    assert len(plan) == 2
    assert plan[0]["vt_symbol"] == "600519.SSE"
    assert plan[0]["side"] == "BUY"
    assert plan[1]["vt_symbol"] == "000858.SZE"
    assert plan[1]["side"] == "SELL"
