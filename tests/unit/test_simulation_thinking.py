"""Simulation thinking feedback tests."""

from src.trading.thinking import (
    build_thinking_review,
    render_thinking_markdown,
    thinking_entry_to_signal_payload,
)


def test_thinking_marks_hold_with_unavailable_price_as_unknown():
    review = build_thinking_review(
        "2026-06-22",
        [
            {
                "symbol": "300599",
                "name": "XiongSu Tech",
                "baseline_price": 12.48,
                "current_price": 0.0,
                "change_pct": 0.0,
                "action": "hold",
                "risk_flags": ["price_unavailable"],
                "execution": {"action_taken": "skipped"},
                "daily_changes": {
                    "position": {"volume": 7600, "avg_cost": 12.17},
                },
            }
        ],
    )

    entry = review["entries"][0]
    assert entry["operation_judgement"] == "unknown"
    assert entry["feedback_signal"] == "hold"
    assert "price_unavailable" in entry["evidence"]["risk_flags"]
    assert thinking_entry_to_signal_payload(entry) is None


def test_thinking_marks_buying_negative_same_day_move_as_incorrect():
    review = build_thinking_review(
        "2026-06-23",
        [
            {
                "symbol": "600519",
                "name": "Kweichow Moutai",
                "baseline_price": 100.0,
                "current_price": 94.0,
                "change_pct": -0.06,
                "action": "buy",
                "risk_flags": [],
                "execution": {"action_taken": "executed"},
                "daily_changes": {"position": None},
            }
        ],
    )

    entry = review["entries"][0]
    assert entry["operation_judgement"] == "incorrect"
    assert entry["feedback_signal"] == "sell"
    assert "thinking_incorrect" in entry["risk_flags"]

    signal = thinking_entry_to_signal_payload(entry)
    assert signal["provider"] == "thinking"
    assert signal["signal"] == "sell"
    assert signal["score"] < 40
    assert "thinking_incorrect" in signal["risks"]


def test_thinking_markdown_summarizes_judgements():
    review = build_thinking_review(
        "2026-06-23",
        [
            {
                "symbol": "600519",
                "name": "Kweichow Moutai",
                "baseline_price": 100.0,
                "current_price": 109.0,
                "change_pct": 0.09,
                "action": "hold",
                "risk_flags": [],
                "execution": {"action_taken": "skipped"},
                "daily_changes": {
                    "position": {"volume": 100, "avg_cost": 100.0},
                },
            }
        ],
    )

    markdown = render_thinking_markdown(review)

    assert "Daily Simulation Thinking" in markdown
    assert "600519" in markdown
    assert "correct" in markdown
