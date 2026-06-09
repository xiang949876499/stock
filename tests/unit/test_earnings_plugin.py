"""财报分析插件测试"""

import pytest
from src.plugins.equity_research.earnings import EarningsAnalysisPlugin


@pytest.fixture
def earnings_plugin():
    return EarningsAnalysisPlugin()


def test_earnings_plugin_name(earnings_plugin):
    assert earnings_plugin.name == "earnings_analysis"


def test_earnings_parameters(earnings_plugin):
    params = earnings_plugin.get_parameters()
    assert "period" in params
    assert "compare_with" in params
    assert "focus_areas" in params


@pytest.mark.asyncio
async def test_earnings_execute(earnings_plugin):
    stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "revenue": 150000000000,
        "net_profit": 75000000000,
        "eps": 59.72,
        "roe": 0.32,
        "gross_margin": 0.91,
        "net_margin": 0.50,
        "operating_cash_flow": 80000000000,
    }

    params = {
        "period": "2024Q3",
        "compare_with": "2023Q3",
        "focus_areas": ["revenue", "margins", "cash_flow"]
    }

    result = await earnings_plugin.execute(stock_data, params)

    assert "summary" in result
    assert "highlights" in result
    assert "risks" in result
    assert "financial_metrics" in result
    assert "yoy_comparison" in result
    assert isinstance(result["highlights"], list)
    assert isinstance(result["risks"], list)
