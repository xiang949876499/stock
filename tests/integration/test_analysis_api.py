"""Analysis API integration tests."""

import pytest
from fastapi.testclient import TestClient

from src.analysis.ai.base import AnalysisResult
from src.main import app
from src.web.deps import get_analysis_service


@pytest.fixture
def client():
    app.dependency_overrides.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_analysis_api_forwards_market_and_date_to_service(client):
    captured = {}

    class FakeAnalysisService:
        async def analyze_stock(self, symbol, strategy_name, context=None):
            captured.update(
                {
                    "symbol": symbol,
                    "strategy_name": strategy_name,
                    "context": context,
                }
            )
            return AnalysisResult(
                score=64,
                signal="hold",
                trend="neutral",
                reason="TradingAgents neutral decision",
            )

    app.dependency_overrides[get_analysis_service] = lambda: FakeAnalysisService()

    response = client.post(
        "/api/v1/analysis/analyze",
        json={
            "symbol": "600519",
            "market": "A",
            "strategy": "tradingagents",
            "analysis_date": "2026-06-16",
        },
    )

    assert response.status_code == 200
    assert response.json()["signal"] == "hold"
    assert captured == {
        "symbol": "600519",
        "strategy_name": "tradingagents",
        "context": {
            "market": "A",
            "analysis_date": "2026-06-16",
        },
    }
