"""LBO 杠杆收购插件测试"""

import pytest
from src.plugins.financial_analysis.lbo import LBOAnalysisPlugin


@pytest.fixture
def lbo_plugin():
    return LBOAnalysisPlugin()


def test_lbo_plugin_name(lbo_plugin):
    assert lbo_plugin.name == "lbo_analysis"


def test_lbo_plugin_description(lbo_plugin):
    assert "LBO" in lbo_plugin.description


def test_lbo_parameters(lbo_plugin):
    params = lbo_plugin.get_parameters()
    assert "purchase_price" in params
    assert "debt_ratio" in params
    assert "interest_rate" in params
    assert "exit_multiple" in params
    assert "holding_period" in params
    assert params["debt_ratio"]["default"] == 0.60
    assert params["holding_period"]["default"] == 5


@pytest.mark.asyncio
async def test_lbo_execute_with_explicit_params(lbo_plugin):
    stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "current_price": 1800.0,
        "ebitda": 50000000000,
        "total_shares": 1256198000,
    }

    params = {
        "purchase_price": 100000000000,
        "debt_ratio": 0.60,
        "interest_rate": 0.05,
        "exit_multiple": 12.0,
        "holding_period": 5,
    }

    result = await lbo_plugin.execute(stock_data, params)

    assert "purchase_price" in result
    assert "equity_invested" in result
    assert "debt_at_entry" in result
    assert "exit_enterprise_value" in result
    assert "exit_equity_value" in result
    assert "moic" in result
    assert "equity_irr_pct" in result
    assert "debt_paydown" in result
    assert "debt_paydown_pct" in result
    assert "yearly_projections" in result
    assert result["purchase_price"] == 100000000000
    assert result["equity_invested"] == 40000000000
    assert result["debt_at_entry"] == 60000000000
    assert len(result["yearly_projections"]) == 5
    assert result["moic"] > 0


@pytest.mark.asyncio
async def test_lbo_execute_with_default_purchase_price(lbo_plugin):
    stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "current_price": 1800.0,
        "ebitda": 50000000000,
        "total_shares": 1256198000,
    }

    params = {
        "debt_ratio": 0.50,
        "interest_rate": 0.06,
        "exit_multiple": 10.0,
        "holding_period": 3,
    }

    result = await lbo_plugin.execute(stock_data, params)

    assert result["purchase_price"] > 0
    assert result["debt_ratio_pct"] == 50.0
    assert len(result["yearly_projections"]) == 3
