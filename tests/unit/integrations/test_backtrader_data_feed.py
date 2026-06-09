import pytest
import pandas as pd
from datetime import datetime
from src.integrations.backtrader.data_feed import DataFrameDataFeed


def test_data_feed_creation():
    """测试数据源创建"""
    df = pd.DataFrame({
        'open': [100.0] * 10,
        'high': [105.0] * 10,
        'low': [95.0] * 10,
        'close': [102.0] * 10,
        'volume': [1000000] * 10,
    }, index=pd.date_range('2024-01-01', periods=10))
    feed = DataFrameDataFeed(dataname=df)
    assert feed is not None


def test_data_feed_from_dataframe():
    """测试 from_dataframe 工厂方法"""
    df = pd.DataFrame({
        'datetime': pd.date_range('2024-01-01', periods=10),
        'open': [100.0] * 10,
        'high': [105.0] * 10,
        'low': [95.0] * 10,
        'close': [102.0] * 10,
        'volume': [1000000] * 10,
    })
    feed = DataFrameDataFeed.from_dataframe(df)
    assert feed is not None


def test_data_feed_column_mapping():
    """测试列名映射"""
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=5),
        'Open': [100.0] * 5,
        'High': [105.0] * 5,
        'Low': [95.0] * 5,
        'Close': [102.0] * 5,
        'Volume': [1000000] * 5,
    })
    feed = DataFrameDataFeed.from_dataframe(df, column_mapping={
        'date': 'datetime',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume',
    })
    assert feed is not None
