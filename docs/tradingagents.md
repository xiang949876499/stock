# TradingAgents Integration

Stock Hub exposes TauricResearch TradingAgents as an optional analysis strategy named `tradingagents`.

## What Is Connected

- Backend strategy names: `tradingagents`, `trading_agents`, `multi_agent`
- API endpoint: `POST /api/v1/analysis/analyze`
- Frontend: `股票分析` page strategy selector, option `TradingAgents 多智能体`
- Upstream entry point: `TradingAgentsGraph.propagate(ticker, trade_date, asset_type="stock")`
- Result mapping: upstream final decision is converted into Stock Hub `score`, `signal`, `trend`, `reason`, and `raw`

## Install

TradingAgents is a heavy optional dependency. Install it only in environments that need multi-agent stock analysis:

```bash
uv sync --extra dev --extra tradingagents
```

For pip-based environments:

```bash
pip install -e ".[tradingagents]"
```

The `all-integrations` extra also includes it:

```bash
pip install -e ".[all-integrations]"
```

## Configuration

Stock Hub maps the existing AI settings into TradingAgents when possible:

| Stock Hub setting | TradingAgents setting |
| --- | --- |
| `AI_PROVIDER=openai` | `llm_provider=openai` |
| `AI_PROVIDER=claude` | `llm_provider=anthropic` |
| `AI_PROVIDER=gemini` | `llm_provider=google` |
| `AI_PROVIDER=qwen` | `llm_provider=dashscope` |
| `AI_PROVIDER=deepseek` | `llm_provider=deepseek` |
| `AI_MODEL` | `deep_think_llm` and `quick_think_llm` |
| `AI_BASE_URL` | `backend_url` |

TradingAgents native environment overrides still take precedence:

```bash
TRADINGAGENTS_LLM_PROVIDER=deepseek
TRADINGAGENTS_DEEP_THINK_LLM=deepseek-reasoner
TRADINGAGENTS_QUICK_THINK_LLM=deepseek-chat
TRADINGAGENTS_LLM_BACKEND_URL=https://api.deepseek.com
TRADINGAGENTS_OUTPUT_LANGUAGE=Chinese
TRADINGAGENTS_SELECTED_ANALYSTS=market,news
TRADINGAGENTS_MAX_DEBATE_ROUNDS=2
TRADINGAGENTS_MAX_RISK_ROUNDS=2
TRADINGAGENTS_CHECKPOINT_ENABLED=true
TRADINGAGENTS_DEBUG=false
TRADINGAGENTS_MAX_ATTEMPTS=2
TRADINGAGENTS_RETRY_BACKOFF_SECONDS=2
```

Provider API keys are read by TradingAgents in its native format. If only Stock Hub `AI_API_KEY` is set, the adapter copies it into the matching provider key when the target variable is empty, such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `DEEPSEEK_API_KEY`, or `DASHSCOPE_API_KEY`.

## API Example

```bash
curl -X POST http://127.0.0.1:8000/api/v1/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "600519",
    "market": "A",
    "strategy": "tradingagents",
    "analysis_date": "2026-06-16"
  }'
```

The adapter converts A-share symbols for TradingAgents/Yahoo:

| Input | Market | Upstream ticker |
| --- | --- | --- |
| `600519` | `A` | `600519.SS` |
| `000001` | `A` | `000001.SZ` |
| `300750` | `A` | `300750.SZ` |
| `0700` | `HK` | `0700.HK` |
| `NVDA` | `US` | `NVDA` |

## Long-Term Simulated Analysis

The simulated trading analyzer now uses a quant long-term baseline by default. TradingAgents remains available as an optional single-stock/multi-agent analysis strategy, but it is no longer the default baseline generator for simulated trading:

- Manual trigger: `POST /api/v1/trading/analyze`
- Startup trigger: one immediate analysis job is scheduled when the simulated trading scheduler starts
- Trading start trigger: `POST /api/v1/trading/start` schedules the first analysis in the background after the engine is marked running
- Pre-market scheduled plan: Monday to Friday 09:00 Asia/Shanghai
- Post-market scheduled review: Monday to Friday 15:35 Asia/Shanghai
- Weekly baseline: when the current ISO week has no baseline, run a deterministic quant screen on 5 A-share candidates and generate a `weekly_analysis` report
- Daily strategy: validate the weekly baseline, generate missing Kronos summaries for candidates, build normalized reasoning signals, and generate a `daily_optimization` report that can drive simulated buy/sell/hold decisions
- Quant execution: weekly quant output never trades directly; daily `QuantLongTermPolicy` is the only long-term path that can call simulated buy/sell
- Evidence sources: quant weekly baseline, optional Vibe-Trading/backtest evidence, optional Kronos forecast evidence from the candidate snapshot, daily technical/news context, and rule checks
- Long-term position sizing: daily quant buys use a conservative 10% single-symbol capital cap

Long-term reports are stored separately from ordinary daily trading reports:

```bash
curl http://127.0.0.1:8000/api/v1/trading/long-term-reports
curl "http://127.0.0.1:8000/api/v1/trading/long-term-reports?type=weekly_analysis"
curl "http://127.0.0.1:8000/api/v1/trading/long-term-reports?type=daily_validation"
curl "http://127.0.0.1:8000/api/v1/trading/long-term-reports?type=daily_optimization"
curl http://127.0.0.1:8000/api/v1/trading/long-term-reports/2026-06-16
```

If the current ISO week has no weekly quant report yet, `POST /api/v1/trading/analyze`, `POST /api/v1/trading/start`, the startup job, or the 09:00 pre-market job creates one first, then immediately runs daily validation and daily optimization for the same trading date. Later calls in the same week reuse the weekly baseline and create fresh daily validation and daily optimization reports.

Daily optimization artifacts are also written to:

```text
data/simulation_reviews/YYYY-MM-DD/report.md
data/simulation_reviews/YYYY-MM-DD/analysis.json
```

When running with Docker Compose, the host `./data` directory is mounted to `/app/data`, so the same files appear on the host under `data/simulation_reviews/`.

Optional Vibe-Trading evidence can be attached to a weekly candidate snapshot under `vibe_trading`:

```json
{
  "symbol": "600519",
  "signal": "buy",
  "score": 86,
  "vibe_trading": {
    "signal": "sell",
    "score": 24,
    "confidence": 0.9,
    "rationale": "Shadow backtest is negative",
    "backtest": {"sharpe": -0.4, "max_drawdown": -0.18}
  }
}
```

Negative Vibe-Trading backtest evidence becomes a quant risk flag and can block a bullish weekly baseline from buying.

Optional Kronos forecast evidence can be attached under `kronos_prediction`:

```json
{
  "symbol": "600519",
  "signal": "buy",
  "score": 86,
  "kronos_prediction": {
    "forecast_return": -0.06,
    "confidence": 0.85,
    "horizon": "10d",
    "rationale": "Kronos forecasts lower closes over the next window"
  }
}
```

Bearish Kronos forecasts become a `kronos_bearish_forecast` risk flag and can block a simulated buy, but they do not bypass `QuantLongTermPolicy`, the simulation executor, or rule checks.

When a weekly candidate does not already include `kronos_prediction`, the daily optimization step tries to generate it immediately before building the quant decision. In the default schedule this happens during the 09:00 Asia/Shanghai pre-market run; it also happens for manual `POST /api/v1/trading/analyze` calls. If Kronos dependencies, model files, or price history are unavailable, the adapter logs a warning and the simulation continues without Kronos evidence.

Runtime knobs:

| Setting / env | Default | Notes |
| --- | --- | --- |
| `KRONOS_ENABLED` | `true` | Set to `false` to disable summary generation. |
| `KRONOS_REPO_PATH` | `../Kronos` | Local clone that exposes `model.KronosPredictor`. |
| `KRONOS_TOKENIZER` | `NeoQuasar/Kronos-Tokenizer-base` | Hugging Face tokenizer id or local path. |
| `KRONOS_MODEL` | `NeoQuasar/Kronos-small` | Hugging Face model id or local path. |
| `KRONOS_LOOKBACK` | `120` | Historical bars passed to Kronos. |
| `KRONOS_PRED_LEN` | `10` | Forecast horizon in business-day bars. |

## Operational Notes

- TradingAgents performs multi-agent LLM analysis and can be slow. The frontend API client timeout is already five minutes.
- For routine simulated trading runs, prefer a conservative profile such as `TRADINGAGENTS_SELECTED_ANALYSTS=market,news`, `TRADINGAGENTS_MAX_DEBATE_ROUNDS=1`, `TRADINGAGENTS_MAX_RISK_ROUNDS=1`, and `TRADINGAGENTS_MAX_ATTEMPTS=2`. This lowers the number of upstream LLM/API calls and retries transient disconnects once before the weekly baseline degrades to hold/skipped.
- `TRADINGAGENTS_MAX_ATTEMPTS` only retries transient provider/network disconnects such as connection resets, remote disconnects, timeouts, or temporarily unavailable responses. Non-transient errors still fail fast so configuration and code issues are visible.
- If the optional dependency is missing, the backend returns an analysis provider error that includes the install command.
- TradingAgents writes its own result/cache/memory files according to its upstream config, including `TRADINGAGENTS_RESULTS_DIR`, `TRADINGAGENTS_CACHE_DIR`, and `TRADINGAGENTS_MEMORY_LOG_PATH`.
- TradingAgents, Vibe-Trading, and Kronos are evidence providers only. They do not bypass Stock Hub's quant policy, simulation executor, or risk checks.

## License boundary

TradingAgents is an optional third-party dependency. The repository root [LICENSE](../LICENSE) applies only to Stock Hub's original contributions and does not replace TradingAgents' Apache-2.0 terms or any required notices. See [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) before distributing an artifact that includes this dependency.
