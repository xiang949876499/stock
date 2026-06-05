"""Parquet 存储测试"""

import pytest
import pandas as pd
from datetime import date
from src.data.storage.parquet import ParquetStorage
from src.data.models import Market


@pytest.fixture
def storage(tmp_path):
    """存储实例"""
    return ParquetStorage(data_dir=str(tmp_path))


@pytest.fixture
def sample_df():
    """样本数据"""
    return pd.DataFrame({
        "date": [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)],
        "symbol": ["600519", "600519", "600519"],
        "market": ["A", "A", "A"],
        "open": [1800.0, 1810.0, 1820.0],
        "high": [1850.0, 1860.0, 1870.0],
        "low": [1790.0, 1800.0, 1810.0],
        "close": [1840.0, 1850.0, 1860.0],
        "volume": [10000, 11000, 12000],
        "amount": [18400000, 20350000, 22320000],
    })


def test_save_and_load(storage, sample_df):
    """测试保存和加载"""
    storage.save_daily(sample_df, "600519", Market.A)
    loaded = storage.load_daily("600519", Market.A)
    assert loaded is not None
    assert len(loaded) == 3
    assert loaded["close"].iloc[0] == 1840.0


def test_load_not_exists(storage):
    """测试加载不存在的数据"""
    loaded = storage.load_daily("999999", Market.A)
    assert loaded is None


def test_exists(storage, sample_df):
    """测试检查存在"""
    assert storage.exists("600519", Market.A) is False
    storage.save_daily(sample_df, "600519", Market.A)
    assert storage.exists("600519", Market.A) is True


def test_get_last_date(storage, sample_df):
    """测试获取最后日期"""
    assert storage.get_last_date("600519", Market.A) is None
    storage.save_daily(sample_df, "600519", Market.A)
    last_date = storage.get_last_date("600519", Market.A)
    assert last_date == date(2026, 1, 3)


def test_load_with_date_filter(storage, sample_df):
    """测试带日期过滤的加载"""
    storage.save_daily(sample_df, "600519", Market.A)
    loaded = storage.load_daily("600519", Market.A)
    assert loaded is not None
    assert len(loaded) == 3


def test_delete(storage, sample_df):
    """测试删除"""
    storage.save_daily(sample_df, "600519", Market.A)
    assert storage.exists("600519", Market.A) is True
    storage.delete("600519", Market.A)
    assert storage.exists("600519", Market.A) is False
