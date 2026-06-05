"""契约测试"""

import pytest
from datetime import datetime
from src.contracts.signals_v1 import SignalV1, SignalStatus, SignalSource
from src.contracts.data_v1 import Market, StockDailyV1, StockInfoV1
from src.contracts.agent_v1 import AgentTool, AGENT_TOOLS


def test_signal_v1():
    """测试信号契约"""
    signal = SignalV1(
        signal_id="test-001",
        as_of=datetime(2026, 1, 1),
        source=SignalSource.MANUAL,
        status=SignalStatus.DRAFT,
        targets={"600519.SSE": 0.3},
    )
    assert signal.schema_version == "v1"
    assert signal.signal_id == "test-001"
    assert signal.source == SignalSource.MANUAL
    assert signal.status == SignalStatus.DRAFT


def test_signal_status_enum():
    """测试信号状态枚举"""
    assert SignalStatus.DRAFT == "draft"
    assert SignalStatus.APPROVED == "approved"
    assert SignalStatus.PUBLISHED == "published"
    assert SignalStatus.REJECTED == "rejected"
    assert SignalStatus.CONSUMED == "consumed"
    assert SignalStatus.ARCHIVED == "archived"


def test_signal_source_enum():
    """测试信号来源枚举"""
    assert SignalSource.QLIB == "qlib"
    assert SignalSource.VNPY_ALPHA == "vnpy_alpha"
    assert SignalSource.MANUAL == "manual"
    assert SignalSource.LLM_PROPOSED == "llm_proposed"
    assert SignalSource.FINRL_X == "finrl_x"


def test_stock_daily_v1():
    """测试日线数据契约"""
    data = StockDailyV1(
        symbol="600519",
        market=Market.A,
        date="2026-01-01",
        open=1800.0,
        high=1850.0,
        low=1790.0,
        close=1840.0,
        volume=10000,
        amount=18400000.0,
        turnover=0.5,
    )
    assert data.symbol == "600519"
    assert data.market == Market.A


def test_agent_tools():
    """测试 Agent 工具"""
    assert len(AGENT_TOOLS) == 5

    tool_names = [t.name for t in AGENT_TOOLS]
    assert "get_stock_price" in tool_names
    assert "get_kline" in tool_names
    assert "get_technical_indicators" in tool_names
    assert "get_news" in tool_names
    assert "analyze_stock" in tool_names


def test_agent_tool_structure():
    """测试 Agent 工具结构"""
    tool = AGENT_TOOLS[0]
    assert isinstance(tool, AgentTool)
    assert tool.name == "get_stock_price"
    assert "symbol" in tool.parameters["properties"]
    assert "market" in tool.parameters["properties"]
