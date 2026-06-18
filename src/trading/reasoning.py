"""Normalized reasoning signals for long-term simulation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReasoningSignal:
    """A normalized signal emitted by a research or quant provider."""

    provider: str
    symbol: str
    name: str = ""
    horizon: str = "long_term"
    signal: str = "hold"
    score: float = 50.0
    confidence: float = 0.5
    rationale: str = ""
    risks: list[str] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    artifact_paths: list[str] = field(default_factory=list)

    def normalized_signal(self) -> str:
        """Return the signal constrained to the engine's action vocabulary."""
        value = (self.signal or "hold").lower()
        return value if value in {"buy", "sell", "hold"} else "hold"

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "symbol": self.symbol,
            "name": self.name,
            "horizon": self.horizon,
            "signal": self.normalized_signal(),
            "score": self.score,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "risks": self.risks,
            "evidence": self.evidence,
            "artifact_paths": self.artifact_paths,
        }

    @classmethod
    def from_candidate(cls, candidate: dict[str, Any]) -> "ReasoningSignal":
        return cls(
            provider=str(candidate.get("provider") or "tradingagents"),
            symbol=str(candidate.get("symbol") or ""),
            name=str(candidate.get("name") or candidate.get("symbol") or ""),
            signal=str(candidate.get("signal") or "hold"),
            score=float(candidate.get("score") or 50),
            confidence=float(candidate.get("confidence") or 0.7),
            rationale=str(candidate.get("reason") or candidate.get("action_reason") or ""),
            risks=list(candidate.get("risks") or []),
            evidence={
                "price": candidate.get("price"),
                "trend": candidate.get("trend"),
                "market": candidate.get("market"),
            },
            artifact_paths=list(candidate.get("artifact_paths") or []),
        )
