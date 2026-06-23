"""Daily thinking feedback for simulated trading decisions."""

from __future__ import annotations

from typing import Any


UNKNOWN_BLOCKERS = {"price_unavailable"}


def build_thinking_review(report_date: str, optimizations: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a daily operation-quality review from optimization rows."""
    entries = [_build_entry(report_date, item) for item in optimizations]
    counts: dict[str, int] = {}
    for entry in entries:
        judgement = entry["operation_judgement"]
        counts[judgement] = counts.get(judgement, 0) + 1
    return {
        "report_date": report_date,
        "summary": {
            "total": len(entries),
            "judgements": counts,
        },
        "entries": entries,
    }


def render_thinking_markdown(review: dict[str, Any]) -> str:
    """Render a human-readable thinking report."""
    rows = []
    details = []
    for entry in review.get("entries", []):
        rows.append(
            "| {symbol} | {action} | {taken} | {change:.2%} | {judgement} | {signal} |".format(
                symbol=entry.get("symbol", ""),
                action=entry.get("action", "hold"),
                taken=entry.get("action_taken", "skipped"),
                change=float(entry.get("evidence", {}).get("change_pct") or 0),
                judgement=entry.get("operation_judgement", "unknown"),
                signal=entry.get("feedback_signal", "hold"),
            )
        )
        details.append(
            "### {symbol} {name}\n\n"
            "- Judgement: {judgement}\n"
            "- Feedback: {signal} / {score:.0f}\n"
            "- Risks: {risks}\n\n"
            "{rationale}".format(
                symbol=entry.get("symbol", ""),
                name=entry.get("name", ""),
                judgement=entry.get("operation_judgement", "unknown"),
                signal=entry.get("feedback_signal", "hold"),
                score=float(entry.get("feedback_score") or 50),
                risks=", ".join(entry.get("risk_flags") or []) or "none",
                rationale=entry.get("rationale", ""),
            )
        )

    table = "\n".join(rows) if rows else "| - | - | - | - | - | - |"
    body = "\n\n".join(details) if details else "No thinking entries."
    return f"""# Daily Simulation Thinking

- Date: {review.get("report_date", "")}
- Purpose: review operation correctness from same-day performance and execution context.

| Symbol | Action | Execution | Change | Judgement | Feedback |
| --- | --- | --- | ---: | --- | --- |
{table}

## Operation Review

{body}
"""


def thinking_entry_to_signal_payload(entry: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a thinking entry to a ReasoningSignal-compatible payload."""
    judgement = entry.get("operation_judgement")
    if judgement == "unknown":
        return None
    return {
        "provider": "thinking",
        "symbol": str(entry.get("symbol") or ""),
        "name": str(entry.get("name") or entry.get("symbol") or ""),
        "signal": str(entry.get("feedback_signal") or "hold"),
        "score": float(entry.get("feedback_score") or 50),
        "confidence": float(entry.get("confidence") or 0.5),
        "rationale": str(entry.get("rationale") or ""),
        "risks": list(entry.get("risk_flags") or []),
        "evidence": dict(entry.get("evidence") or {}),
        "artifact_paths": list(entry.get("artifact_paths") or []),
    }


def _build_entry(report_date: str, item: dict[str, Any]) -> dict[str, Any]:
    evidence = _extract_evidence(item)
    judgement, signal, score, confidence, risks, rationale = _judge_operation(item, evidence)
    # Sync evidence risk_flags with thinking-appended flags so consumers see a
    # consistent view regardless of which path they read.
    evidence["risk_flags"] = risks
    return {
        "report_date": report_date,
        "symbol": str(item.get("symbol") or ""),
        "name": str(item.get("name") or item.get("symbol") or ""),
        "action": str(item.get("action") or "hold"),
        "action_taken": str(item.get("execution", {}).get("action_taken") or "skipped"),
        "operation_judgement": judgement,
        "feedback_signal": signal,
        "feedback_score": score,
        "confidence": confidence,
        "risk_flags": risks,
        "rationale": rationale,
        "evidence": evidence,
    }


def _extract_evidence(item: dict[str, Any]) -> dict[str, Any]:
    position = (item.get("daily_changes") or {}).get("position")
    risk_flags = list(item.get("risk_flags") or [])
    baseline_price = float(item.get("baseline_price") or 0)
    current_price = float(item.get("current_price") or 0)
    change_pct = float(item.get("change_pct") or 0)
    position_pnl_pct = None
    if isinstance(position, dict):
        avg_cost = float(position.get("avg_cost") or 0)
        if avg_cost and current_price:
            position_pnl_pct = (current_price - avg_cost) / avg_cost
    return {
        "baseline_price": baseline_price,
        "current_price": current_price,
        "change_pct": change_pct,
        "risk_flags": risk_flags,
        "position": position,
        "position_pnl_pct": position_pnl_pct,
    }


def _judge_operation(
    item: dict[str, Any],
    evidence: dict[str, Any],
) -> tuple[str, str, float, float, list[str], str]:
    action = str(item.get("action") or "hold")
    action_taken = str(item.get("execution", {}).get("action_taken") or "skipped")
    change_pct = float(evidence.get("change_pct") or 0)
    current_price = float(evidence.get("current_price") or 0)
    baseline_price = float(evidence.get("baseline_price") or 0)
    risk_flags = list(evidence.get("risk_flags") or [])
    position = evidence.get("position")
    has_position = isinstance(position, dict) and int(position.get("volume") or 0) > 0

    if current_price <= 0 or baseline_price <= 0 or UNKNOWN_BLOCKERS.intersection(risk_flags):
        return (
            "unknown",
            "hold",
            50.0,
            0.1,
            risk_flags,
            "Price or baseline data was unavailable, so the operation cannot be judged.",
        )

    if action == "sell":
        if action_taken == "executed" and (
            change_pct <= -0.04 or "review_drawdown" in risk_flags
        ):
            return (
                "correct",
                "sell",
                70.0,
                0.75,
                risk_flags,
                "Selling aligned with same-day drawdown or explicit risk controls.",
            )
        return (
            "questionable",
            "hold",
            45.0,
            0.6,
            _with_flag(risk_flags, "thinking_questionable"),
            "Selling did not have clear same-day loss or risk confirmation.",
        )

    if action == "buy":
        if action_taken == "executed" and change_pct < -0.03:
            return (
                "incorrect",
                "sell",
                32.0,
                0.82,
                _with_flag(risk_flags, "thinking_incorrect"),
                "Buying conflicted with a negative same-day move.",
            )
        if action_taken == "executed" and change_pct >= 0.02:
            return (
                "correct",
                "buy",
                68.0,
                0.7,
                risk_flags,
                "Buying aligned with positive same-day confirmation.",
            )
        return (
            "questionable",
            "hold",
            46.0,
            0.55,
            _with_flag(risk_flags, "thinking_questionable"),
            "Buying lacked clear same-day confirmation.",
        )

    if has_position and (change_pct <= -0.08 or "review_drawdown" in risk_flags):
        return (
            "incorrect",
            "sell",
            34.0,
            0.78,
            _with_flag(risk_flags, "thinking_incorrect"),
            "Holding a position through a large drawdown conflicts with risk control.",
        )
    if has_position and change_pct < 0:
        return (
            "questionable",
            "hold",
            48.0,
            0.55,
            _with_flag(risk_flags, "thinking_questionable"),
            "Holding through a moderate intraday decline warrants review.",
        )
    if has_position and change_pct >= 0:
        return (
            "correct",
            "hold",
            62.0,
            0.62,
            risk_flags,
            "Holding was consistent with non-negative same-day performance.",
        )
    if not has_position and change_pct >= 0.06:
        return (
            "questionable",
            "hold",
            48.0,
            0.5,
            _with_flag(risk_flags, "thinking_questionable"),
            "Holding avoided risk but may have missed a strong same-day move.",
        )
    return (
        "correct",
        "hold",
        56.0,
        0.55,
        risk_flags,
        "Holding was conservative and consistent with available same-day evidence.",
    )


def _with_flag(flags: list[str], flag: str) -> list[str]:
    """Return a new list with *flag* appended, or a copy if already present."""
    return [*flags] if flag in flags else [*flags, flag]
