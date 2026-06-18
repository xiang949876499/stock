"""Quant-governed long-term simulation policy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.trading.reasoning import ReasoningSignal


@dataclass(slots=True)
class QuantDecision:
    """Executable decision produced by the long-term quant policy."""

    symbol: str
    name: str
    action: str
    signal: str
    score: float
    target_weight: float
    allocation_pct: float
    executable: bool
    rationale: str
    risk_flags: list[str] = field(default_factory=list)
    provider_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "action": self.action,
            "signal": self.signal,
            "score": self.score,
            "target_weight": self.target_weight,
            "allocation_pct": self.allocation_pct,
            "executable": self.executable,
            "rationale": self.rationale,
            "risk_flags": self.risk_flags,
            "provider_breakdown": self.provider_breakdown,
        }


class QuantLongTermPolicy:
    """Aggregate research evidence into constrained simulated orders."""

    provider_weights = {
        "quant_screen": 1.0,
        "tradingagents": 1.0,
        "tradingagents_cn": 1.0,
        "vibe_trading": 1.2,
        "kronos": 1.1,
        "technical": 0.8,
        "rules": 1.1,
    }

    def __init__(
        self,
        max_single_position_pct: float = 0.10,
        buy_score_threshold: float = 65.0,
        sell_score_threshold: float = 38.0,
        drawdown_stop_pct: float = -0.08,
    ):
        self.max_single_position_pct = max_single_position_pct
        self.buy_score_threshold = buy_score_threshold
        self.sell_score_threshold = sell_score_threshold
        self.drawdown_stop_pct = drawdown_stop_pct

    def decide(
        self,
        symbol: str,
        name: str,
        current_price: float,
        baseline_price: float,
        position: dict[str, Any] | None,
        rule_checks: list[dict[str, Any]],
        signals: list[ReasoningSignal],
    ) -> QuantDecision:
        provider_breakdown = {s.provider: s.to_dict() for s in signals}
        risk_flags = self._collect_risk_flags(
            current_price=current_price,
            baseline_price=baseline_price,
            rule_checks=rule_checks,
            signals=signals,
        )
        score = self._aggregate_score(signals)
        direction = self._aggregate_direction(signals)
        signal = self._direction_to_signal(direction, score)

        has_position = bool(position)
        executable = current_price > 0
        action = "hold"
        target_weight = 0.0
        allocation_pct = 0.0

        if has_position and (
            score <= self.sell_score_threshold
            or direction <= -0.35
            or "review_drawdown" in risk_flags
            or "blocking_rules" in risk_flags
        ):
            action = "sell"
            signal = "sell"
            target_weight = 0.0
        elif (
            not has_position
            and signal == "buy"
            and score >= self.buy_score_threshold
            and not self._has_buy_blocker(risk_flags)
        ):
            action = "buy"
            target_weight = self.max_single_position_pct
            allocation_pct = min(self.max_single_position_pct, 0.10)
        elif has_position:
            action = "hold"
            target_weight = self.max_single_position_pct

        if not executable:
            action = "hold"
            allocation_pct = 0.0

        return QuantDecision(
            symbol=symbol,
            name=name,
            action=action,
            signal=signal,
            score=score,
            target_weight=target_weight,
            allocation_pct=allocation_pct,
            executable=executable and action in {"buy", "sell"},
            rationale=self._build_rationale(
                score=score,
                direction=direction,
                action=action,
                risk_flags=risk_flags,
                signals=signals,
                position=position,
            ),
            risk_flags=risk_flags,
            provider_breakdown=provider_breakdown,
        )

    def _aggregate_score(self, signals: list[ReasoningSignal]) -> float:
        if not signals:
            return 50.0
        weighted_total = 0.0
        weight_sum = 0.0
        for signal in signals:
            weight = self.provider_weights.get(signal.provider, 0.7)
            confidence = max(0.1, min(float(signal.confidence or 0.5), 1.0))
            effective_weight = weight * confidence
            weighted_total += float(signal.score or 50) * effective_weight
            weight_sum += effective_weight
        return round(weighted_total / weight_sum, 2) if weight_sum else 50.0

    def _aggregate_direction(self, signals: list[ReasoningSignal]) -> float:
        if not signals:
            return 0.0
        mapping = {"buy": 1.0, "hold": 0.0, "sell": -1.0}
        weighted_total = 0.0
        weight_sum = 0.0
        for signal in signals:
            weight = self.provider_weights.get(signal.provider, 0.7)
            confidence = max(0.1, min(float(signal.confidence or 0.5), 1.0))
            effective_weight = weight * confidence
            weighted_total += mapping[signal.normalized_signal()] * effective_weight
            weight_sum += effective_weight
        return round(weighted_total / weight_sum, 3) if weight_sum else 0.0

    def _collect_risk_flags(
        self,
        current_price: float,
        baseline_price: float,
        rule_checks: list[dict[str, Any]],
        signals: list[ReasoningSignal],
    ) -> list[str]:
        flags: list[str] = []
        if current_price <= 0:
            flags.append("price_unavailable")
        if baseline_price and current_price:
            change_pct = (current_price - baseline_price) / baseline_price
            if change_pct <= self.drawdown_stop_pct:
                flags.append("review_drawdown")
        if any(not item.get("passed") for item in rule_checks):
            flags.append("blocking_rules")
        for signal in signals:
            for risk in signal.risks:
                if risk not in flags:
                    flags.append(risk)
            if signal.provider == "vibe_trading" and signal.normalized_signal() == "sell":
                if "negative_backtest" not in flags:
                    flags.append("negative_backtest")
            if signal.provider == "kronos" and signal.normalized_signal() == "sell":
                if "kronos_bearish_forecast" not in flags:
                    flags.append("kronos_bearish_forecast")
        return flags

    def _has_buy_blocker(self, risk_flags: list[str]) -> bool:
        blockers = {
            "price_unavailable",
            "blocking_rules",
            "negative_backtest",
            "kronos_bearish_forecast",
            "review_drawdown",
        }
        return any(flag in blockers for flag in risk_flags)

    def _direction_to_signal(self, direction: float, score: float) -> str:
        if direction >= 0.25 and score >= self.buy_score_threshold:
            return "buy"
        if direction <= -0.25 or score <= self.sell_score_threshold:
            return "sell"
        return "hold"

    def _build_rationale(
        self,
        score: float,
        direction: float,
        action: str,
        risk_flags: list[str],
        signals: list[ReasoningSignal],
        position: dict[str, Any] | None,
    ) -> str:
        providers = ", ".join(signal.provider for signal in signals) or "none"
        tradingagents = next(
            (signal for signal in signals if signal.provider.startswith("tradingagents")),
            None,
        )
        kronos = next((signal for signal in signals if signal.provider == "kronos"), None)
        parts = [
            f"Quant score {score:.2f}, aggregate direction {direction:.2f}.",
            f"Providers considered: {providers}.",
        ]
        if tradingagents:
            parts.append(
                "TradingAgents baseline: "
                f"{tradingagents.normalized_signal()} / {tradingagents.score:.0f}."
            )
        if kronos:
            parts.append(
                "Kronos forecast: "
                f"{kronos.normalized_signal()} / {kronos.score:.0f}."
            )
        if position:
            parts.append(
                "Existing simulated position: "
                f"{position.get('volume', 0)} shares at {position.get('avg_cost', 0)}."
            )
        else:
            parts.append("No existing simulated position.")
        if risk_flags:
            parts.append(f"Risk flags: {', '.join(risk_flags)}.")
        parts.append(f"Quant action: {action}.")
        return " ".join(parts)
