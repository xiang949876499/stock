"""数据模型"""

from datetime import datetime, date
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class Market(str, Enum):
    """市场类型"""
    A = "A"      # A股
    HK = "HK"    # 港股
    US = "US"    # 美股


class StockDaily(BaseModel):
    """日线数据"""
    symbol: str
    market: Market
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float
    turnover: float = Field(description="换手率")
    adj_factor: float = Field(default=1.0, description="复权因子")


class StockInfo(BaseModel):
    """股票基本信息"""
    symbol: str
    name: str
    market: Market
    industry: str
    list_date: date
    delist_date: Optional[date] = None
    is_st: bool = False
    is_active: bool = True


class FinancialData(BaseModel):
    """财务数据"""
    symbol: str
    market: Market
    report_date: date
    revenue: float
    net_profit: float
    eps: float
    roe: float
    pe_ratio: float
    pb_ratio: float


class NewsItem(BaseModel):
    """新闻数据"""
    id: str
    symbol: str
    market: Market
    title: str
    content: str
    source: str
    url: str
    publish_time: datetime
    sentiment: str = Field(description="positive/negative/neutral")
    importance: str = Field(description="P0/P1/P2")


class TechnicalIndicators(BaseModel):
    """技术指标"""
    symbol: str
    market: Market
    date: date
    ma5: float
    ma10: float
    ma20: float
    ma60: float
    macd: float
    macd_signal: float
    macd_hist: float
    kdj_k: float
    kdj_d: float
    kdj_j: float
    rsi_6: float
    rsi_12: float
    rsi_24: float
    boll_upper: float
    boll_middle: float
    boll_lower: float
