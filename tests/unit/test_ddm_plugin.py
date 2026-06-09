"""DDM 股息贴现估值插件测试"""

import pytest
from src.plugins.financial_analysis.ddm import DDMValuationPlugin


@pytest.fixture
def ddm_plugin():
    return DDMValuationPlugin()


def test_ddm_plugin_name(ddm_plugin):
    assert ddm_plugin.name == "ddm_valuation"


def test_ddm_plugin_description(ddm_plugin):
    assert "DDM" in ddm_plugin.description


def test_ddm_parameters(ddm_plugin):
    params = ddm_plugin.get_parameters()
    assert "dividend_per_share" in params
    assert "growth_rate" in params
    assert "required_return" in params
    assert "years" in params
    assert params["growth_rate"]["default"] == 0.05
    assert params["required_return"]["default"] == 0.10


@pytest.mark.asyncio
async def test_ddm_execute_with_valid_params(ddm_plugin):
    stock_data = {
        "symbol": "601398",
        "name": "工商银行",
        "current_price": 5.0,
    }

    params = {
        "dividend_per_share": 0.30,
        "growth_rate": 0.03,
        "required_return": 0.10,
        "years": 10,
    }

    result = await ddm_plugin.execute(stock_data, params)

    assert "intrinsic_value" in result
    assert "current_price" in result
    assert "upside_pct" in result
    assert "dividend_per_share" in result
    assert "growth_rate_pct" in result
    assert "required_return_pct" in result
    assert "dividend_yield_pct" in result
    assert "pv_dividends" in result
    assert "terminal_value" in result
    assert "pv_terminal_value" in result
    assert "dividend_projections" in result
    assert result["intrinsic_value"] > 0
    assert len(result["dividend_projections"]) == 10
    assert result["growth_rate_pct"] == 3.0
    assert result["required_return_pct"] == 10.0


@pytest.mark.asyncio
async def test_ddm_execute_with_zero_dividend(ddm_plugin):
    stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "current_price": 1800.0,
    }

    params = {
        "dividend_per_share": 0,
        "growth_rate": 0.05,
        "required_return": 0.10,
    }

    result = await ddm_plugin.execute(stock_data, params)

    assert "error" in result
    assert result["intrinsic_value"] == 0


@pytest.mark.asyncio
async def test_ddm_execute_with_invalid_rates(ddm_plugin):
    stock_data = {
        "symbol": "601398",
        "name": "工商银行",
        "current_price": 5.0,
    }

    params = {
        "dividend_per_share": 0.30,
        "growth_rate": 0.15,
        "required_return": 0.10,
    }

    result = await ddm_plugin.execute(stock_data, params)

    assert "error" in result
    assert "回报率" in result["error"]


@pytest.mark.asyncio
async def test_ddm_execute_from_stock_data(ddm_plugin):
    """测试从 stock_data 中获取股息数据"""
    stock_data = {
        "symbol": "601398",
        "name": "工商银行",
        "current_price": 5.0,
        "dividend_per_share": 0.25,
    }

    params = {
        "growth_rate": 0.02,
        "required_return": 0.10,
        "years": 5,
    }

    result = await ddm_plugin.execute(stock_data, params)

    assert result["intrinsic_value"] > 0
    assert result["dividend_per_share"] == 0.25
    assert len(result["dividend_projections"]) == 5
