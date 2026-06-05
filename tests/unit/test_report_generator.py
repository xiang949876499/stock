"""报告生成器测试"""

import pytest
import asyncio
from src.analysis.report.generator import ReportGenerator


@pytest.fixture
def generator():
    """报告生成器实例"""
    return ReportGenerator()


@pytest.mark.asyncio
async def test_generate_decision_dashboard(generator):
    """测试生成决策仪表盘"""
    dashboard = await generator.generate_decision_dashboard(
        stock_name="贵州茅台",
        stock_code="600519",
        score=85,
        signal="buy",
        trend="bullish",
        reason="技术面看多，MACD 金叉",
        risk_alerts=["估值偏高", "短期涨幅过大"],
        catalysts=["业绩超预期", "机构增持"],
        target_price=1900.0,
        stop_loss=1750.0,
    )

    assert "贵州茅台" in dashboard
    assert "600519" in dashboard
    assert "85" in dashboard
    assert "买入" in dashboard
    assert "看多" in dashboard
    assert "估值偏高" in dashboard
    assert "业绩超预期" in dashboard
    assert "1900" in dashboard
    assert "1750" in dashboard


@pytest.mark.asyncio
async def test_generate_decision_dashboard_minimal(generator):
    """测试生成最小决策仪表盘"""
    dashboard = await generator.generate_decision_dashboard(
        stock_name="五粮液",
        stock_code="000858",
        score=50,
        signal="hold",
        trend="neutral",
        reason="震荡行情",
    )

    assert "五粮液" in dashboard
    assert "000858" in dashboard
    assert "50" in dashboard
    assert "持有" in dashboard


@pytest.mark.asyncio
async def test_generate_market_review(generator):
    """测试生成大盘复盘"""
    indices = [
        {"name": "上证指数", "price": 3250.12, "change": "+0.85%"},
        {"name": "深证成指", "price": 10521.36, "change": "+1.02%"},
    ]

    sectors = [
        {"name": "互联网服务", "change": "+2.5%"},
        {"name": "文化传媒", "change": "+1.8%"},
    ]

    stats = {
        "up_count": 3920,
        "down_count": 1349,
        "limit_up": 155,
        "limit_down": 3,
    }

    review = await generator.generate_market_review(indices, sectors, stats)

    assert "上证指数" in review
    assert "3250.12" in review
    assert "互联网服务" in review
    assert "3920" in review
