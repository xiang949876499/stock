"""Optional Kronos forecast adapter for simulated trading evidence."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import get_settings
from src.data.models import Market
from src.data.service import DataService


@dataclass(slots=True)
class KronosAdapter:
    """Generate compact Kronos summaries for simulation candidates."""

    enabled: bool | None = None
    repo_path: str | None = None
    tokenizer_name: str | None = None
    model_name: str | None = None
    lookback: int | None = None
    pred_len: int | None = None
    min_history: int | None = None
    sample_count: int | None = None

    def __post_init__(self):
        settings = get_settings()
        self.enabled = settings.kronos_enabled if self.enabled is None else self.enabled
        self.repo_path = self.repo_path or settings.kronos_repo_path
        self.tokenizer_name = self.tokenizer_name or settings.kronos_tokenizer
        self.model_name = self.model_name or settings.kronos_model
        self.lookback = self.lookback or settings.kronos_lookback
        self.pred_len = self.pred_len or settings.kronos_pred_len
        self.min_history = self.min_history or min(self.lookback, 90)
        self.sample_count = self.sample_count or settings.kronos_sample_count
        self._predictor = None
        self._data_service = DataService()

    async def summarize_candidate(
        self,
        candidate: dict[str, Any],
        analysis_date: date,
    ) -> dict[str, Any] | None:
        if not self.enabled:
            return None

        symbol = str(candidate.get("symbol") or "")
        if not symbol:
            return None

        history = await self._load_history(symbol, analysis_date)
        if history.empty or len(history) < self.min_history:
            return None

        predictor = self._load_predictor()
        window = history.tail(self.lookback).copy()
        x_timestamp = pd.to_datetime(window["timestamps"])
        y_timestamp = self._future_timestamps(x_timestamp.iloc[-1], self.pred_len)
        pred_df = predictor.predict(
            df=window[["open", "high", "low", "close", "volume", "amount"]],
            x_timestamp=x_timestamp,
            y_timestamp=y_timestamp,
            pred_len=self.pred_len,
            T=0.8,
            top_p=0.9,
            sample_count=self.sample_count,
            verbose=False,
        )

        last_close = float(window["close"].iloc[-1])
        forecast_close = float(pred_df["close"].iloc[-1])
        forecast_return = (
            (forecast_close - last_close) / last_close if last_close else 0.0
        )
        return {
            "forecast_return": round(forecast_return, 6),
            "predicted_close": round(forecast_close, 4),
            "current_price": round(last_close, 4),
            "confidence": self._confidence_from_return(forecast_return),
            "horizon": f"{self.pred_len}d",
            "source": "kronos",
            "rationale": (
                "Kronos forecast return "
                f"{forecast_return:.2%} over the next {self.pred_len} bars"
            ),
        }

    async def _load_history(self, symbol: str, analysis_date: date) -> pd.DataFrame:
        start_date = analysis_date - timedelta(days=max(self.lookback * 3, 240))
        raw = await self._data_service.get_daily(
            symbol=symbol,
            market=Market.A,
            start_date=start_date,
            end_date=analysis_date,
        )
        if raw is None or raw.empty:
            return pd.DataFrame()
        return self._normalize_history(raw)

    def _load_predictor(self):
        if self._predictor is not None:
            return self._predictor

        repo = Path(self.repo_path).expanduser()
        if not repo.exists():
            raise RuntimeError(f"Kronos repo path does not exist: {repo}")
        repo_str = str(repo)
        if repo_str not in sys.path:
            sys.path.insert(0, repo_str)

        from model import Kronos, KronosPredictor, KronosTokenizer

        tokenizer = KronosTokenizer.from_pretrained(self.tokenizer_name)
        model = Kronos.from_pretrained(self.model_name)
        self._predictor = KronosPredictor(model, tokenizer, max_context=self.lookback)
        return self._predictor

    @staticmethod
    def _normalize_history(raw: pd.DataFrame) -> pd.DataFrame:
        df = raw.copy()
        rename_map = {
            "date": "timestamps",
            "datetime": "timestamps",
            "vol": "volume",
            "amt": "amount",
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
        if "timestamps" not in df.columns:
            df["timestamps"] = df.index
        if "volume" not in df.columns:
            df["volume"] = 0.0
        if "amount" not in df.columns:
            df["amount"] = 0.0
        required = ["timestamps", "open", "high", "low", "close", "volume", "amount"]
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Kronos history missing columns: {', '.join(missing)}")
        df = df[required].dropna(subset=["open", "high", "low", "close"])
        df["timestamps"] = pd.to_datetime(df["timestamps"])
        return df.sort_values("timestamps")

    @staticmethod
    def _future_timestamps(last_timestamp, pred_len: int) -> pd.Series:
        start = pd.Timestamp(last_timestamp).normalize() + pd.Timedelta(days=1)
        return pd.Series(pd.bdate_range(start=start, periods=pred_len))

    @staticmethod
    def _confidence_from_return(forecast_return: float) -> float:
        return round(max(0.55, min(0.9, 0.55 + abs(forecast_return) * 4.0)), 3)
