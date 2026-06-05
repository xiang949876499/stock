"""数据契约 v1"""

from datetime import datetime, date
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field


class Market(str, Enum):
    """市场类型"""
    A = "A"      # A股
    HK = "HK"    # 港股
    US = "US"    # 美股


class StockDailyV1(BaseModel):
    """日线数据契约"""
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


class StockInfoV1(BaseModel):
    """股票基本信息契约"""
    symbol: str
    name: str
    market: Market
    industry: str
    list_date: date
    delist_date: Optional[date] = None
    is_st: bool = False
    is_active: bool = True
