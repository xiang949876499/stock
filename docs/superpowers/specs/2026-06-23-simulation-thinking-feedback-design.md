# Simulation Thinking Feedback Design

## Goal

Create a separate daily thinking layer for simulated trading that reviews whether each operation was correct using same-day performance and execution context, then feeds that judgement into later buy/sell decisions.

## Architecture

Daily optimization remains the source of execution decisions. After it finishes, the engine writes a separate thinking artifact under `data/simulation_thinking/<report_date>/` with both human-readable Markdown and machine-readable JSON. Later daily optimization runs load the most recent prior thinking entry for each symbol and append it as a `thinking` reasoning provider.

## Data Flow

1. `run_daily_long_term_validation()` builds validations and optimizations as it does today.
2. The engine saves the normal optimization report under `data/simulation_reviews/<date>/`.
3. The engine evaluates each optimization row against current price, baseline price, held position, execution result, risk flags, and action.
4. The engine writes:
   - `data/simulation_thinking/<date>/thinking.md`
   - `data/simulation_thinking/<date>/thinking.json`
5. On later runs, `_build_daily_optimizations()` loads the latest thinking entry before the current report date for the same symbol and includes it in `reasoning_signals`.

## Judgement Rules

The judgement is intentionally conservative:

- `unknown`: price is unavailable, baseline is unavailable, or risk flags include `price_unavailable`.
- `correct`: action matches visible performance/risk, such as selling a drawdown, holding during unavailable price data, holding a positive held position, or buying into a positive move without blockers.
- `questionable`: action is defensible but weak, such as holding while a non-held candidate has a strong positive move, or holding a held position with mild negative performance.
- `incorrect`: action conflicts with performance/risk, such as buying while same-day evidence is negative or holding a held position through a large drawdown.

## Decision Influence

The thinking artifact becomes a `thinking` `ReasoningSignal`:

- `correct`: positive score and confidence.
- `questionable`: neutral-to-negative score and `thinking_questionable` risk.
- `incorrect`: negative score and `thinking_incorrect` risk.
- `unknown`: not loaded as a decision signal.

`QuantLongTermPolicy` treats `thinking` like another provider with moderate weight. Incorrect or questionable feedback blocks new buys and can reduce confidence in future holds.

## Testing

Unit tests cover:

- thinking artifacts are created beside daily optimization artifacts.
- operation judgement uses same-day performance and execution context.
- prior thinking feedback is loaded into the next day's optimization provider breakdown.
- the quant policy blocks a buy when thinking feedback marks the prior operation incorrect.
