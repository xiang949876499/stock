"""股票筛选插件测试"""

import pytest
from src.plugins.financial_analysis.screening import StockScreeningPlugin


@pytest.fixture
def screening_plugin():
    return StockScreeningPlugin()


def test_screening_plugin_name(screening_plugin):
    assert screening_plugin.name == "stock_screening"


def test_screening_parameters(screening_plugin):
    params = screening_plugin.get_parameters()
    assert "universe" in params
    assert "filters" in params
    assert "sort_by" in params
    assert "limit" in params


@pytest.mark.asyncio
async def test_screening_execute(screening_plugin):
    stock_data = {}
    params = {
        "universe": "hs300",
        "filters": {
            "pe_ratio": {"max": 30},
            "roe": {"min": 0.15}
        },
        "sort_by": "roe",
        "limit": 5
    }

    result = await screening_plugin.execute(stock_data, params)

    assert "results" in result
    assert "total_count" in result
    assert "filters_applied" in result
    assert len(result["results"]) <= 5
