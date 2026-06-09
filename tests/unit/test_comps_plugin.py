"""可比公司分析插件测试"""

import pytest
from src.plugins.financial_analysis.comps import ComparableAnalysisPlugin


@pytest.fixture
def comps_plugin():
    return ComparableAnalysisPlugin()


def test_comps_plugin_name(comps_plugin):
    assert comps_plugin.name == "comparable_analysis"


def test_comps_parameters(comps_plugin):
    params = comps_plugin.get_parameters()
    assert "peer_codes" in params
    assert "metrics" in params


@pytest.mark.asyncio
async def test_comps_execute(comps_plugin):
    stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "current_price": 1800.0,
        "pe_ratio": 30.5,
        "pb_ratio": 10.2,
        "ps_ratio": 15.8,
        "ev_ebitda": 22.3,
    }

    params = {
        "peer_codes": ["000858", "002304", "000568"],
        "metrics": ["PE", "PB", "PS", "EV/EBITDA"],
    }

    result = await comps_plugin.execute(stock_data, params)

    assert "target_valuation" in result
    assert "peer_comparison" in result
    assert "implied_value" in result
    assert "premium_discount" in result
    assert len(result["peer_comparison"]) == 3
