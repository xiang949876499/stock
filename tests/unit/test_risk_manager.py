"""风控管理器测试"""

import pytest
import asyncio
from src.execution.risk.risk_manager import RiskManager, RiskConfig, RiskCheckResult
from src.research.signals.generator import Signal, SignalStatus, SignalSource


@pytest.fixture
def risk_manager():
    """风控管理器实例"""
    return RiskManager()


@pytest.fixture
def valid_signal():
    """有效信号"""
    return Signal(
        signal_id="test-001",
        as_of="2026-01-01T00:00:00",
        source=SignalSource.MANUAL,
        status=SignalStatus.PUBLISHED,
        targets={
            "600519.SSE": 0.08,
            "000858.SZE": 0.07,
        },
    )


@pytest.mark.asyncio
async def test_check_signal_valid(risk_manager, valid_signal):
    """测试检查有效信号"""
    result = await risk_manager.check_signal(valid_signal)
    assert result.passed is True


@pytest.mark.asyncio
async def test_check_signal_over_weight(risk_manager):
    """测试检查超重信号"""
    signal = Signal(
        signal_id="test-002",
        as_of="2026-01-01T00:00:00",
        source=SignalSource.MANUAL,
        status=SignalStatus.PUBLISHED,
        targets={
            "600519.SSE": 0.6,
            "000858.SZE": 0.6,
        },
    )
    result = await risk_manager.check_signal(signal)
    assert result.passed is False
    assert "总权重" in result.reason


@pytest.mark.asyncio
async def test_check_signal_single_over_limit(risk_manager):
    """测试检查单标的超限"""
    signal = Signal(
        signal_id="test-003",
        as_of="2026-01-01T00:00:00",
        source=SignalSource.MANUAL,
        status=SignalStatus.PUBLISHED,
        targets={
            "600519.SSE": 0.5,
        },
        risk_overlay={"max_single_name_weight": 0.3},
    )
    result = await risk_manager.check_signal(signal)
    assert result.passed is False
    assert "超过上限" in result.reason


def test_update_pnl(risk_manager):
    """测试更新盈亏"""
    risk_manager.update_pnl(100.0)
    assert risk_manager.daily_pnl == 100.0

    risk_manager.update_pnl(-50.0)
    assert risk_manager.daily_pnl == 50.0


def test_reset_daily(risk_manager):
    """测试重置每日统计"""
    risk_manager.update_pnl(100.0)
    risk_manager.reset_daily()
    assert risk_manager.daily_pnl == 0.0
