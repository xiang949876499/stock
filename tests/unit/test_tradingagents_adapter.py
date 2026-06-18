"""TradingAgents adapter tests."""

import sys
import types

import pytest

from src.analysis.ai.base import AnalysisResult
from src.analysis.tradingagents_adapter import (
    TradingAgentsAdapter,
    TradingAgentsConfig,
    normalize_tradingagents_symbol,
)
from src.config import Settings


def _install_fake_tradingagents(monkeypatch, decision):
    calls = []

    tradingagents_pkg = types.ModuleType("tradingagents")
    graph_pkg = types.ModuleType("tradingagents.graph")
    default_config_mod = types.ModuleType("tradingagents.default_config")
    graph_mod = types.ModuleType("tradingagents.graph.trading_graph")

    default_config_mod.DEFAULT_CONFIG = {
        "llm_provider": "openai",
        "deep_think_llm": "gpt-5.5",
        "quick_think_llm": "gpt-5.4-mini",
        "backend_url": None,
        "output_language": "English",
        "checkpoint_enabled": False,
        "max_debate_rounds": 1,
        "max_risk_discuss_rounds": 1,
    }

    class FakeTradingAgentsGraph:
        def __init__(self, selected_analysts, debug, config):
            calls.append(
                {
                    "selected_analysts": selected_analysts,
                    "debug": debug,
                    "config": config,
                }
            )

        def propagate(self, ticker, trade_date, asset_type="stock"):
            calls.append(
                {
                    "ticker": ticker,
                    "trade_date": trade_date,
                    "asset_type": asset_type,
                }
            )
            current_decision = decision() if callable(decision) else decision
            return {"state": "ok"}, current_decision

    graph_mod.TradingAgentsGraph = FakeTradingAgentsGraph

    monkeypatch.setitem(sys.modules, "tradingagents", tradingagents_pkg)
    monkeypatch.setitem(sys.modules, "tradingagents.graph", graph_pkg)
    monkeypatch.setitem(sys.modules, "tradingagents.default_config", default_config_mod)
    monkeypatch.setitem(sys.modules, "tradingagents.graph.trading_graph", graph_mod)

    return calls


@pytest.mark.parametrize(
    ("symbol", "market", "expected"),
    [
        ("600519", "A", "600519.SS"),
        ("000001", "A", "000001.SZ"),
        ("300750", "A", "300750.SZ"),
        ("600519.SS", "A", "600519.SS"),
        ("0700", "HK", "0700.HK"),
        ("NVDA", "US", "NVDA"),
    ],
)
def test_normalize_tradingagents_symbol(symbol, market, expected):
    assert normalize_tradingagents_symbol(symbol, market) == expected


def test_from_settings_maps_ai_settings_to_tradingagents_config(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings = Settings(
        ai_provider="openai",
        ai_api_key="sk-test",
        ai_model="gpt-test",
        ai_base_url="https://example.test/v1",
    )

    config = TradingAgentsConfig.from_settings(settings)

    assert config.llm_provider == "openai"
    assert config.deep_think_llm == "gpt-test"
    assert config.quick_think_llm == "gpt-test"
    assert config.backend_url == "https://example.test/v1"
    assert config.output_language == "Chinese"
    assert config.env_api_keys["OPENAI_API_KEY"] == "sk-test"


def test_from_settings_reads_tradingagents_runtime_knobs(monkeypatch):
    monkeypatch.setenv("TRADINGAGENTS_MAX_DEBATE_ROUNDS", "1")
    monkeypatch.setenv("TRADINGAGENTS_MAX_RISK_ROUNDS", "1")
    monkeypatch.setenv("TRADINGAGENTS_CHECKPOINT_ENABLED", "true")
    monkeypatch.setenv("TRADINGAGENTS_DEBUG", "true")
    monkeypatch.setenv("TRADINGAGENTS_SELECTED_ANALYSTS", "market,news")
    monkeypatch.setenv("TRADINGAGENTS_MAX_ATTEMPTS", "3")
    monkeypatch.setenv("TRADINGAGENTS_RETRY_BACKOFF_SECONDS", "0.25")

    config = TradingAgentsConfig.from_settings(
        Settings(ai_provider="deepseek", ai_api_key="")
    )

    assert config.max_debate_rounds == 1
    assert config.max_risk_discuss_rounds == 1
    assert config.checkpoint_enabled is True
    assert config.debug is True
    assert config.selected_analysts == ("market", "news")
    assert config.max_attempts == 3
    assert config.retry_backoff_seconds == 0.25


@pytest.mark.asyncio
async def test_adapter_invokes_tradingagents_graph_and_parses_buy_signal(monkeypatch):
    calls = _install_fake_tradingagents(
        monkeypatch,
        {
            "action": "Buy",
            "confidence": 0.82,
            "trend": "bullish",
            "rationale": "fundamentals and technical analysts agree",
        },
    )
    adapter = TradingAgentsAdapter(
        TradingAgentsConfig(
            llm_provider="deepseek",
            deep_think_llm="deepseek-reasoner",
            quick_think_llm="deepseek-chat",
            max_debate_rounds=2,
            checkpoint_enabled=True,
            debug=True,
        )
    )

    result = await adapter.analyze_stock("600519", market="A", analysis_date="2026-06-16")

    assert isinstance(result, AnalysisResult)
    assert result.signal == "buy"
    assert result.trend == "bullish"
    assert result.score == 82
    assert "fundamentals" in result.reason
    assert calls[0]["debug"] is True
    assert calls[0]["config"]["llm_provider"] == "deepseek"
    assert calls[0]["config"]["max_debate_rounds"] == 2
    assert calls[0]["config"]["checkpoint_enabled"] is True
    assert calls[1] == {
        "ticker": "600519.SS",
        "trade_date": "2026-06-16",
        "asset_type": "stock",
    }


@pytest.mark.asyncio
async def test_adapter_parses_chinese_sell_signal(monkeypatch):
    _install_fake_tradingagents(monkeypatch, "建议卖出，风险偏高，趋势看空，评分 28")
    adapter = TradingAgentsAdapter(TradingAgentsConfig())

    result = await adapter.analyze_stock("000001", market="A", analysis_date="2026-06-16")

    assert result.signal == "sell"
    assert result.trend == "bearish"
    assert result.score == 28


@pytest.mark.asyncio
async def test_adapter_retries_transient_connection_errors(monkeypatch):
    attempts = 0

    def flaky_decision():
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise ConnectionResetError(10054, "remote host closed connection")
        return {
            "action": "Hold",
            "confidence": 0.51,
            "trend": "neutral",
            "rationale": "retry succeeded",
        }

    _install_fake_tradingagents(monkeypatch, flaky_decision)
    adapter = TradingAgentsAdapter(
        TradingAgentsConfig(max_attempts=2, retry_backoff_seconds=0)
    )

    result = await adapter.analyze_stock("000001", market="A", analysis_date="2026-06-16")

    assert attempts == 2
    assert result.signal == "hold"
    assert result.score == 51
    assert "retry succeeded" in result.reason
