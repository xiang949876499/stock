"""StockPicker tests."""

from unittest.mock import AsyncMock

import pytest

from src.analysis.strategies.stock_picker import StockPicker
from src.data.models import Market


class _Catalog:
    mapping = {
        "000001": {"name": "平安银行", "market": "A"},
        "600519": {"name": "贵州茅台", "market": "A"},
        "00700": {"name": "腾讯控股", "market": "HK"},
    }


class _DataService:
    catalog = _Catalog()


@pytest.mark.asyncio
async def test_recommend_can_skip_duplicate_ai_screening():
    """Simulation can select technical Top N before its full decision analysis."""
    picker = StockPicker(data_service=_DataService())
    picker._quick_screen = AsyncMock(
        return_value=[
            {"symbol": "600519", "name": "贵州茅台", "market": "A", "score": 90},
            {"symbol": "000001", "name": "平安银行", "market": "A", "score": 80},
        ]
    )
    picker._ai_deep_screen = AsyncMock()
    progress = []

    result = await picker.recommend(
        Market.A,
        top_n=1,
        use_ai_screen=False,
        progress_callback=progress.append,
    )

    assert [stock["symbol"] for stock in result] == ["600519"]
    picker._ai_deep_screen.assert_not_awaited()
    assert progress[-1] == "技术快筛完成：2 只有效候选，选取 Top 1 进入交易决策"
