"""Quant long-term policy tests."""

from src.trading.quant_policy import QuantLongTermPolicy
from src.trading.reasoning import ReasoningSignal


def test_policy_buys_only_when_multi_source_evidence_is_positive():
    policy = QuantLongTermPolicy()
    decision = policy.decide(
        symbol="600519",
        name="Kweichow Moutai",
        current_price=100.0,
        baseline_price=98.0,
        position=None,
        rule_checks=[],
        signals=[
            ReasoningSignal(
                provider="tradingagents",
                symbol="600519",
                name="Kweichow Moutai",
                signal="buy",
                score=82,
                confidence=0.75,
                rationale="Long-term thesis is constructive",
            ),
            ReasoningSignal(
                provider="vibe_trading",
                symbol="600519",
                name="Kweichow Moutai",
                signal="buy",
                score=78,
                confidence=0.8,
                rationale="Shadow backtest has positive expectancy",
            ),
        ],
    )

    assert decision.action == "buy"
    assert decision.executable is True
    assert decision.allocation_pct > 0
    assert decision.target_weight <= policy.max_single_position_pct
    assert decision.signal == "buy"
    assert decision.provider_breakdown["vibe_trading"]["signal"] == "buy"


def test_policy_blocks_buy_when_vibe_backtest_is_negative():
    policy = QuantLongTermPolicy()
    decision = policy.decide(
        symbol="600519",
        name="Kweichow Moutai",
        current_price=100.0,
        baseline_price=100.0,
        position=None,
        rule_checks=[],
        signals=[
            ReasoningSignal(
                provider="tradingagents",
                symbol="600519",
                signal="buy",
                score=86,
                confidence=0.8,
                rationale="TradingAgents is bullish",
            ),
            ReasoningSignal(
                provider="vibe_trading",
                symbol="600519",
                signal="sell",
                score=28,
                confidence=0.9,
                rationale="Backtest drawdown and expectancy are poor",
                risks=["negative_backtest"],
            ),
        ],
    )

    assert decision.action == "hold"
    assert decision.executable is False
    assert "negative_backtest" in decision.risk_flags
    assert "TradingAgents" in decision.rationale


def test_policy_blocks_buy_when_kronos_forecast_is_bearish():
    policy = QuantLongTermPolicy()
    decision = policy.decide(
        symbol="600519",
        name="Kweichow Moutai",
        current_price=100.0,
        baseline_price=100.0,
        position=None,
        rule_checks=[],
        signals=[
            ReasoningSignal(
                provider="tradingagents",
                symbol="600519",
                signal="buy",
                score=86,
                confidence=0.8,
                rationale="TradingAgents is bullish",
            ),
            ReasoningSignal(
                provider="kronos",
                symbol="600519",
                signal="sell",
                score=30,
                confidence=0.85,
                rationale="Kronos forecasts a negative price path",
                risks=["kronos_bearish_forecast"],
                evidence={"forecast_return": -0.06},
            ),
        ],
    )

    assert decision.action == "hold"
    assert decision.executable is False
    assert "kronos_bearish_forecast" in decision.risk_flags
    assert decision.provider_breakdown["kronos"]["signal"] == "sell"


def test_policy_blocks_buy_when_thinking_feedback_is_incorrect():
    policy = QuantLongTermPolicy()
    decision = policy.decide(
        symbol="600519",
        name="Kweichow Moutai",
        current_price=103.0,
        baseline_price=100.0,
        position=None,
        rule_checks=[],
        signals=[
            ReasoningSignal(
                provider="tradingagents",
                symbol="600519",
                signal="buy",
                score=88,
                confidence=0.82,
                rationale="TradingAgents is bullish",
            ),
            ReasoningSignal(
                provider="thinking",
                symbol="600519",
                signal="sell",
                score=32,
                confidence=0.82,
                rationale="Prior operation was judged incorrect.",
                risks=["thinking_incorrect"],
            ),
        ],
    )

    assert decision.action == "hold"
    assert decision.executable is False
    assert "thinking_incorrect" in decision.risk_flags
    assert decision.provider_breakdown["thinking"]["signal"] == "sell"


def test_policy_sells_held_position_on_quant_risk_break():
    policy = QuantLongTermPolicy()
    decision = policy.decide(
        symbol="600519",
        name="Kweichow Moutai",
        current_price=91.0,
        baseline_price=100.0,
        position={"symbol": "600519", "volume": 100, "avg_cost": 100.0},
        rule_checks=[],
        signals=[
            ReasoningSignal(
                provider="tradingagents",
                symbol="600519",
                signal="buy",
                score=78,
                confidence=0.7,
                rationale="Weekly thesis remains constructive",
            )
        ],
    )

    assert decision.action == "sell"
    assert decision.executable is True
    assert "review_drawdown" in decision.risk_flags
