# Simulation Thinking Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a separate daily thinking feedback layer that reviews operation correctness and feeds prior judgements into later simulated buy/sell decisions.

**Architecture:** Add a focused `src/trading/thinking.py` module for judgement, Markdown rendering, JSON persistence payloads, and signal conversion. `SimulationEngine` will call that module after daily optimization and load the latest prior thinking entry before building the next day's reasoning signals. `QuantLongTermPolicy` will treat `thinking` as a moderate-weight provider and block buys on negative feedback risks.

**Tech Stack:** Python, pytest, SQLite-backed existing simulation engine, JSON/Markdown artifact files.

---

### Task 1: Thinking Judgement Module

**Files:**
- Create: `src/trading/thinking.py`
- Test: `tests/unit/test_simulation_thinking.py`

- [x] **Step 1: Write failing tests**

Add tests that call `build_thinking_review()` with positive, drawdown, and price-unavailable optimization rows. Assert `correct`, `incorrect`/`questionable`, and `unknown` judgements plus Markdown/JSON fields.

- [x] **Step 2: Run tests to verify RED**

Run: `pytest tests/unit/test_simulation_thinking.py -q`

Expected: import failure because `src.trading.thinking` does not exist.

- [x] **Step 3: Implement module**

Create `ThinkingEntry`, `build_thinking_review()`, `render_thinking_markdown()`, and `thinking_entry_to_signal_payload()` with deterministic conservative rules from the design.

- [x] **Step 4: Run tests to verify GREEN**

Run: `pytest tests/unit/test_simulation_thinking.py -q`

Expected: all tests pass.

### Task 2: Engine Artifact Persistence

**Files:**
- Modify: `src/trading/engine.py`
- Test: `tests/unit/test_simulation_engine.py`

- [x] **Step 1: Write failing engine test**

Extend daily optimization tests so `run_daily_long_term_validation()` creates `data/simulation_thinking/<date>/thinking.md` and `thinking.json`, and returns artifact paths under `thinking_artifacts`.

- [x] **Step 2: Run focused test to verify RED**

Run: `pytest tests/unit/test_simulation_engine.py::test_daily_long_term_validation_creates_optimization_report -q`

Expected: failure because thinking artifacts are not created yet.

- [x] **Step 3: Implement persistence**

Add `self.thinking_output_dir`, `_save_thinking_artifacts()`, and a call from `run_daily_long_term_validation()` after optimization artifacts are saved.

- [x] **Step 4: Run focused test to verify GREEN**

Run: `pytest tests/unit/test_simulation_engine.py::test_daily_long_term_validation_creates_optimization_report -q`

Expected: pass.

### Task 3: Feedback Signal Injection

**Files:**
- Modify: `src/trading/engine.py`
- Modify: `src/trading/quant_policy.py`
- Test: `tests/unit/test_simulation_engine.py`
- Test: `tests/unit/test_quant_long_term_policy.py`

- [x] **Step 1: Write failing tests**

Add an engine test that places prior-day `thinking.json` with an incorrect judgement and asserts the next optimization row includes `provider_breakdown.thinking`. Add a policy test that a `thinking_incorrect` risk blocks a new buy.

- [x] **Step 2: Run focused tests to verify RED**

Run: `pytest tests/unit/test_simulation_engine.py::test_daily_optimization_uses_prior_thinking_feedback tests/unit/test_quant_long_term_policy.py::test_policy_blocks_buy_when_thinking_feedback_is_incorrect -q`

Expected: failure because thinking loading/provider weighting is not implemented.

- [x] **Step 3: Implement loading and policy integration**

Add `_load_latest_thinking_entry()`, `_thinking_reasoning_signal()`, append the signal in `_build_daily_optimizations()`, add a `thinking` provider weight, and treat `thinking_incorrect` / `thinking_questionable` as buy blockers.

- [x] **Step 4: Run focused tests to verify GREEN**

Run: `pytest tests/unit/test_simulation_engine.py::test_daily_optimization_uses_prior_thinking_feedback tests/unit/test_quant_long_term_policy.py::test_policy_blocks_buy_when_thinking_feedback_is_incorrect -q`

Expected: pass.

### Task 4: Regression Verification

**Files:**
- Existing tests only.

- [x] **Step 1: Run focused simulation and policy tests**

Run: `pytest tests/unit/test_simulation_thinking.py tests/unit/test_quant_long_term_policy.py tests/unit/test_simulation_engine.py -q`

Expected: pass or report unrelated pre-existing failures with exact names.

- [x] **Step 2: Inspect git diff**

Run: `git diff -- src/trading/thinking.py src/trading/engine.py src/trading/quant_policy.py tests/unit/test_simulation_thinking.py tests/unit/test_simulation_engine.py tests/unit/test_quant_long_term_policy.py docs/superpowers/specs/2026-06-23-simulation-thinking-feedback-design.md docs/superpowers/plans/2026-06-23-simulation-thinking-feedback.md`

Expected: only scoped thinking feedback changes plus the existing user edits in touched files.
