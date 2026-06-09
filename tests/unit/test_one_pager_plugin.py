"""公司一页纸概述插件测试"""

import pytest
from src.plugins.equity_research.one_pager import OnePagerPlugin


@pytest.fixture
def one_pager_plugin():
    return OnePagerPlugin()


def test_one_pager_plugin_name(one_pager_plugin):
    assert one_pager_plugin.name == "company_one_pager"


def test_one_pager_plugin_description(one_pager_plugin):
    assert "一页纸" in one_pager_plugin.description


def test_one_pager_parameters(one_pager_plugin):
    params = one_pager_plugin.get_parameters()
    assert "symbol" in params
    assert "include_financials" in params
    assert "include_peers" in params
    assert params["include_financials"]["default"] is True
    assert params["include_peers"]["default"] is False


@pytest.mark.asyncio
async def test_one_pager_execute_with_known_symbol(one_pager_plugin):
    stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "current_price": 1800.0,
        "revenue": 150000000000,
        "net_profit": 75000000000,
        "eps": 59.72,
        "roe": 0.32,
        "gross_margin": 0.91,
        "net_margin": 0.50,
        "pe_ratio": 30.0,
        "pb_ratio": 10.0,
        "ps_ratio": 15.0,
        "market_cap": 2260000000000,
    }

    params = {
        "symbol": "600519",
        "include_financials": True,
        "include_peers": False,
    }

    result = await one_pager_plugin.execute(stock_data, params)

    assert "overview" in result
    assert "business" in result
    assert "valuation" in result
    assert "risks" in result
    assert "financial_summary" in result
    assert result["overview"]["name"] == "贵州茅台"
    assert result["overview"]["symbol"] == "600519"
    assert "茅台" in result["business"]["description"]
    assert len(result["business"]["competitive_advantages"]) > 0
    assert len(result["business"]["key_products"]) > 0
    assert result["valuation"]["current_price"] == 1800.0
    assert result["financial_summary"]["eps"] == 59.72


@pytest.mark.asyncio
async def test_one_pager_execute_without_financials(one_pager_plugin):
    stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "current_price": 1800.0,
    }

    params = {
        "symbol": "600519",
        "include_financials": False,
    }

    result = await one_pager_plugin.execute(stock_data, params)

    assert "overview" in result
    assert "business" in result
    assert "valuation" in result
    assert "financial_summary" not in result


@pytest.mark.asyncio
async def test_one_pager_execute_with_peers_flag(one_pager_plugin):
    stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "current_price": 1800.0,
    }

    params = {
        "symbol": "600519",
        "include_financials": False,
        "include_peers": True,
    }

    result = await one_pager_plugin.execute(stock_data, params)

    assert "peers_note" in result
    assert "comparable_analysis" in result["peers_note"]


@pytest.mark.asyncio
async def test_one_pager_execute_with_unknown_symbol(one_pager_plugin):
    stock_data = {
        "symbol": "999999",
        "name": "测试股票",
        "current_price": 10.0,
    }

    params = {
        "symbol": "999999",
        "include_financials": True,
    }

    result = await one_pager_plugin.execute(stock_data, params)

    assert "overview" in result
    assert result["overview"]["name"] == "测试股票"
    assert "business" in result
    assert result["valuation"]["current_price"] == 10.0
