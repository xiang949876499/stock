"""DCF 估值插件测试"""

import pytest
from src.plugins.financial_analysis.dcf import DCFValuationPlugin


@pytest.fixture
def dcf_plugin():
    return DCFValuationPlugin()


def test_dcf_plugin_name(dcf_plugin):
    assert dcf_plugin.name == "dcf_valuation"


def test_dcf_plugin_description(dcf_plugin):
    assert "DCF" in dcf_plugin.description


def test_dcf_parameters(dcf_plugin):
    params = dcf_plugin.get_parameters()
    assert "years" in params
    assert "growth_rate" in params
    assert "wacc" in params
    assert params["years"]["default"] == 5


@pytest.mark.asyncio
async def test_dcf_execute_with_mock_data(dcf_plugin):
    stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "current_price": 1800.0,
        "revenue": 150000000000,
        "net_profit": 75000000000,
        "total_shares": 1256198000,
    }

    params = {
        "years": 5,
        "growth_rate": 0.15,
        "terminal_growth": 0.03,
        "wacc": 0.10,
    }

    result = await dcf_plugin.execute(stock_data, params)

    assert "enterprise_value" in result
    assert "equity_value" in result
    assert "per_share_value" in result
    assert "current_price" in result
    assert "upside_pct" in result
    assert "cash_flows" in result
    assert result["enterprise_value"] > 0
    assert result["per_share_value"] > 0
    assert len(result["cash_flows"]) == 5
