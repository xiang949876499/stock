"""数据模型测试"""

import pytest
from datetime import date, datetime
from src.data.models import (
    Market, StockDaily, StockInfo, FinancialData, NewsItem, TechnicalIndicators
)


def test_market_enum():
    """测试市场枚举"""
    assert Market.A == "A"
    assert Market.HK == "HK"
    assert Market.US == "US"


def test_stock_daily():
    """测试日线数据模型"""
    data = StockDaily(
        symbol="600519",
        market=Market.A,
        date=date(2026, 1, 1),
        open=1800.0,
        high=1850.0,
        low=1790.0,
        close=1840.0,
        volume=10000,
        amount=18400000.0,
        turnover=0.5,
        adj_factor=1.0,
    )
    assert data.symbol == "600519"
    assert data.market == Market.A
    assert data.close == 1840.0


def test_stock_info():
    """测试股票信息模型"""
    info = StockInfo(
        symbol="600519",
        name="贵州茅台",
        market=Market.A,
        industry="白酒",
        list_date=date(2001, 8, 27),
        is_st=False,
        is_active=True,
    )
    assert info.symbol == "600519"
    assert info.name == "贵州茅台"
    assert info.is_st is False


def test_financial_data():
    """测试财务数据模型"""
    data = FinancialData(
        symbol="600519",
        market=Market.A,
        report_date=date(2025, 12, 31),
        revenue=1000000000.0,
        net_profit=500000000.0,
        eps=5.0,
        roe=0.3,
        pe_ratio=30.0,
        pb_ratio=10.0,
    )
    assert data.symbol == "600519"
    assert data.roe == 0.3


def test_news_item():
    """测试新闻数据模型"""
    news = NewsItem(
        id="test_001",
        symbol="600519",
        market=Market.A,
        title="贵州茅台发布财报",
        content="...",
        source="eastmoney",
        url="https://example.com",
        publish_time=datetime(2026, 1, 1, 12, 0, 0),
        sentiment="positive",
        importance="P0",
    )
    assert news.id == "test_001"
    assert news.sentiment == "positive"


def test_technical_indicators():
    """测试技术指标模型"""
    indicators = TechnicalIndicators(
        symbol="600519",
        market=Market.A,
        date=date(2026, 1, 1),
        ma5=1800.0,
        ma10=1790.0,
        ma20=1780.0,
        ma60=1750.0,
        macd=10.0,
        macd_signal=8.0,
        macd_hist=2.0,
        kdj_k=70.0,
        kdj_d=65.0,
        kdj_j=80.0,
        rsi_6=60.0,
        rsi_12=58.0,
        rsi_24=55.0,
        boll_upper=1850.0,
        boll_middle=1800.0,
        boll_lower=1750.0,
    )
    assert indicators.symbol == "600519"
    assert indicators.macd == 10.0
