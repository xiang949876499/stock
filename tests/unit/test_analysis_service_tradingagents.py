"""Analysis service TradingAgents delegation tests."""

import pytest

from src.analysis.ai.base import AnalysisResult
from src.analysis.service import AnalysisService


@pytest.mark.asyncio
async def test_analysis_service_delegates_tradingagents_strategy(monkeypatch):
    captured = {}

    class FakeTradingAgentsAdapter:
        async def analyze_stock(self, symbol, market="A", analysis_date=None):
            captured.update(
                {
                    "symbol": symbol,
                    "market": market,
                    "analysis_date": analysis_date,
                }
            )
            return AnalysisResult(
                score=76,
                signal="buy",
                trend="bullish",
                reason="TradingAgents decision",
                raw="raw",
            )

    monkeypatch.setattr(
        "src.analysis.tradingagents_adapter.TradingAgentsAdapter",
        lambda: FakeTradingAgentsAdapter(),
    )

    service = AnalysisService(ai_adapter=None)
    result = await service.analyze_stock(
        "600519",
        "tradingagents",
        context={"market": "A", "analysis_date": "2026-06-16"},
    )

    assert result.signal == "buy"
    assert captured == {
        "symbol": "600519",
        "market": "A",
        "analysis_date": "2026-06-16",
    }
