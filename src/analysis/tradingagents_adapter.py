"""TradingAgents integration adapter."""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from src.analysis.ai.base import AnalysisResult
from src.config import Settings, get_settings
from src.infra.logger import get_logger

logger = get_logger("tradingagents_adapter")

TRADINGAGENTS_STRATEGY_NAMES = {"tradingagents", "trading_agents", "multi_agent"}


class TradingAgentsUnavailableError(RuntimeError):
    """Raised when the optional TradingAgents package is not installed."""


@dataclass
class TradingAgentsConfig:
    """Runtime options passed from Stock Hub into TradingAgents."""

    llm_provider: str | None = None
    deep_think_llm: str | None = None
    quick_think_llm: str | None = None
    backend_url: str | None = None
    output_language: str | None = "Chinese"
    max_debate_rounds: int | None = None
    max_risk_discuss_rounds: int | None = None
    checkpoint_enabled: bool | None = None
    debug: bool = False
    selected_analysts: tuple[str, ...] = ("market", "social", "news", "fundamentals")
    max_attempts: int = 1
    retry_backoff_seconds: float = 0.0
    extra: dict[str, Any] = field(default_factory=dict)
    env_api_keys: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> "TradingAgentsConfig":
        settings = settings or get_settings()
        provider = _to_tradingagents_provider(settings.ai_provider)
        api_key_env = _provider_api_key_env(provider)
        env_api_keys = {}
        if api_key_env and settings.ai_api_key and not os.getenv(api_key_env):
            env_api_keys[api_key_env] = settings.ai_api_key

        return cls(
            llm_provider=os.getenv("TRADINGAGENTS_LLM_PROVIDER") or provider,
            deep_think_llm=os.getenv("TRADINGAGENTS_DEEP_THINK_LLM") or settings.ai_model,
            quick_think_llm=os.getenv("TRADINGAGENTS_QUICK_THINK_LLM") or settings.ai_model,
            backend_url=os.getenv("TRADINGAGENTS_LLM_BACKEND_URL") or settings.ai_base_url,
            output_language=os.getenv("TRADINGAGENTS_OUTPUT_LANGUAGE") or "Chinese",
            max_debate_rounds=_env_int("TRADINGAGENTS_MAX_DEBATE_ROUNDS"),
            max_risk_discuss_rounds=_env_int(
                "TRADINGAGENTS_MAX_RISK_ROUNDS",
                "TRADINGAGENTS_MAX_RISK_DISCUSS_ROUNDS",
            ),
            checkpoint_enabled=_env_bool("TRADINGAGENTS_CHECKPOINT_ENABLED"),
            debug=_env_bool("TRADINGAGENTS_DEBUG", default=False),
            selected_analysts=_env_tuple(
                "TRADINGAGENTS_SELECTED_ANALYSTS",
                default=("market", "social", "news", "fundamentals"),
            ),
            max_attempts=_env_int("TRADINGAGENTS_MAX_ATTEMPTS", default=1) or 1,
            retry_backoff_seconds=_env_float(
                "TRADINGAGENTS_RETRY_BACKOFF_SECONDS",
                default=0.0,
            )
            or 0.0,
            env_api_keys=env_api_keys,
        )


def normalize_tradingagents_symbol(symbol: str, market: str = "A") -> str:
    """Convert Stock Hub symbols into TradingAgents/Yahoo compatible tickers."""

    cleaned = symbol.strip().upper()
    if not cleaned:
        return cleaned
    if "." in cleaned or "=" in cleaned or "-" in cleaned:
        return cleaned

    market_upper = market.upper()
    if market_upper == "A":
        if cleaned.startswith(("6", "9")):
            return f"{cleaned}.SS"
        if cleaned.startswith(("0", "2", "3")):
            return f"{cleaned}.SZ"
    if market_upper == "HK" and cleaned.isdigit():
        return f"{cleaned}.HK"
    return cleaned


class TradingAgentsAdapter:
    """Runs TauricResearch TradingAgents and maps its result into Stock Hub."""

    def __init__(self, config: TradingAgentsConfig | None = None):
        self.config = config or TradingAgentsConfig.from_settings()

    async def analyze_stock(
        self,
        symbol: str,
        market: str = "A",
        analysis_date: str | None = None,
    ) -> AnalysisResult:
        ticker = normalize_tradingagents_symbol(symbol, market)
        trade_date = analysis_date or date.today().isoformat()
        return await asyncio.to_thread(self._run, ticker, trade_date)

    def _run(self, ticker: str, trade_date: str) -> AnalysisResult:
        attempts = max(1, self.config.max_attempts)
        for attempt in range(1, attempts + 1):
            try:
                return self._run_once(ticker, trade_date)
            except Exception as exc:
                should_retry = (
                    attempt < attempts and _is_transient_external_error(exc)
                )
                if not should_retry:
                    raise
                logger.warning(
                    "TradingAgents transient error on attempt %s/%s for %s: %s",
                    attempt,
                    attempts,
                    ticker,
                    exc,
                )
                if self.config.retry_backoff_seconds > 0:
                    time.sleep(self.config.retry_backoff_seconds)

        raise RuntimeError("TradingAgents retry loop exited unexpectedly")

    def _run_once(self, ticker: str, trade_date: str) -> AnalysisResult:
        TradingAgentsGraph, default_config = self._load_tradingagents()
        config = self._build_upstream_config(default_config)
        graph = TradingAgentsGraph(
            selected_analysts=self.config.selected_analysts,
            debug=self.config.debug,
            config=config,
        )
        state, decision = graph.propagate(ticker, trade_date, asset_type="stock")
        return self._decision_to_result(decision, state)

    def _load_tradingagents(self):
        try:
            from tradingagents.default_config import DEFAULT_CONFIG
            from tradingagents.graph.trading_graph import TradingAgentsGraph
        except ImportError as exc:
            raise TradingAgentsUnavailableError(
                "TradingAgents 未安装。请安装可选依赖："
                "pip install git+https://github.com/TauricResearch/TradingAgents.git"
            ) from exc
        return TradingAgentsGraph, DEFAULT_CONFIG

    def _build_upstream_config(self, default_config: dict[str, Any]) -> dict[str, Any]:
        for key, value in self.config.env_api_keys.items():
            os.environ.setdefault(key, value)

        config = dict(default_config)
        overlay = {
            "llm_provider": self.config.llm_provider,
            "deep_think_llm": self.config.deep_think_llm,
            "quick_think_llm": self.config.quick_think_llm,
            "backend_url": self.config.backend_url,
            "output_language": self.config.output_language,
            "max_debate_rounds": self.config.max_debate_rounds,
            "max_risk_discuss_rounds": self.config.max_risk_discuss_rounds,
            "checkpoint_enabled": self.config.checkpoint_enabled,
        }
        for key, value in overlay.items():
            if value is not None:
                config[key] = value
        config.update(self.config.extra)
        return config

    def _decision_to_result(self, decision: Any, state: Any = None) -> AnalysisResult:
        raw = _to_text(decision)
        signal = _extract_signal(decision, raw)
        score = _extract_score(decision, raw, signal)
        trend = _extract_trend(decision, raw, signal)
        reason = _extract_reason(decision, raw)
        if state is not None and raw == reason:
            raw = _to_text({"decision": decision, "state": state})
        return AnalysisResult(
            score=score,
            signal=signal,
            trend=trend,
            reason=reason,
            raw=raw,
        )


def _to_tradingagents_provider(provider: str) -> str:
    provider_map = {
        "claude": "anthropic",
        "gemini": "google",
        "qwen": "dashscope",
    }
    return provider_map.get(provider.lower(), provider.lower())


def _provider_api_key_env(provider: str) -> str | None:
    return {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "dashscope": "DASHSCOPE_API_KEY",
    }.get(provider)


def _env_first(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value not in (None, ""):
            return value
    return None


def _env_int(*names: str, default: int | None = None) -> int | None:
    value = _env_first(*names)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning("Ignoring invalid integer environment value for %s: %s", names[0], value)
        return default


def _env_float(*names: str, default: float | None = None) -> float | None:
    value = _env_first(*names)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        logger.warning("Ignoring invalid float environment value for %s: %s", names[0], value)
        return default


def _env_bool(*names: str, default: bool | None = None) -> bool | None:
    value = _env_first(*names)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    logger.warning("Ignoring invalid boolean environment value for %s: %s", names[0], value)
    return default


def _env_tuple(*names: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = _env_first(*names)
    if value is None:
        return default
    parsed = tuple(item.strip() for item in value.split(",") if item.strip())
    return parsed or default


def _is_transient_external_error(error: Exception) -> bool:
    text = f"{type(error).__name__}: {error}".lower()
    transient_markers = (
        "connection aborted",
        "connectionreseterror",
        "connection reset",
        "remote host closed connection",
        "remote end closed connection",
        "remotedisconnected",
        "timed out",
        "timeout",
        "temporarily unavailable",
        "server disconnected",
    )
    return any(marker in text for marker in transient_markers)


def _to_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except TypeError:
        return str(value)


def _find_first_value(value: Any, keys: set[str]) -> Any:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in keys:
                return item
        for item in value.values():
            found = _find_first_value(item, keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_first_value(item, keys)
            if found is not None:
                return found
    return None


def _extract_signal(decision: Any, raw: str) -> str:
    explicit = _find_first_value(decision, {"action", "decision", "recommendation", "signal"})
    text = f"{explicit or ''} {raw}".lower()

    hold_terms = ("hold", "neutral", "wait", "观望", "持有", "中性")
    sell_terms = ("sell", "short", "bearish", "reduce", "avoid", "卖出", "减仓", "看空")
    buy_terms = ("buy", "long", "bullish", "accumulate", "买入", "增持", "看多")

    if any(term in text for term in sell_terms):
        return "sell"
    if any(term in text for term in buy_terms):
        return "buy"
    if any(term in text for term in hold_terms):
        return "hold"
    return "hold"


def _extract_score(decision: Any, raw: str, signal: str) -> float:
    explicit = _find_first_value(decision, {"score", "confidence", "rating"})
    score = _coerce_score(explicit)
    if score is None:
        score = _score_from_text(raw)
    if score is None:
        score = {"buy": 75.0, "sell": 35.0, "hold": 50.0}[signal]
    return max(0.0, min(100.0, score))


def _coerce_score(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
    else:
        match = re.search(r"\d+(?:\.\d+)?", str(value))
        if not match:
            return None
        number = float(match.group(0))
    return number * 100 if 0 <= number <= 1 else number


def _score_from_text(raw: str) -> float | None:
    patterns = (
        r"(?:score|confidence|rating|评分|置信度)\D{0,12}(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*/\s*100",
    )
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.IGNORECASE)
        if match:
            return _coerce_score(match.group(1))
    return None


def _extract_trend(decision: Any, raw: str, signal: str) -> str:
    explicit = _find_first_value(decision, {"trend", "market_trend", "outlook"})
    text = f"{explicit or ''} {raw}".lower()
    if any(term in text for term in ("bearish", "negative", "downtrend", "看空", "下行")):
        return "bearish"
    if any(term in text for term in ("bullish", "positive", "uptrend", "看多", "上行")):
        return "bullish"
    return {"buy": "bullish", "sell": "bearish", "hold": "neutral"}[signal]


def _extract_reason(decision: Any, raw: str) -> str:
    explicit = _find_first_value(
        decision,
        {
            "reason",
            "rationale",
            "analysis",
            "final_trade_decision",
            "investment_plan",
            "recommendation",
        },
    )
    if explicit:
        return _to_text(explicit)
    return raw
