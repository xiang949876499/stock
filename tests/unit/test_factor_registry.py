"""因子注册表测试"""

import pytest
import pandas as pd
from src.research.factors.base import FactorRegistry, BuiltinFactors, create_default_registry


@pytest.fixture
def registry():
    """因子注册表实例"""
    return create_default_registry()


@pytest.fixture
def sample_df():
    """样本数据"""
    return pd.DataFrame({
        "close": [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110],
        "volume": [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000],
    })


def test_list_factors(registry):
    """测试列出因子"""
    factors = registry.list_factors()
    assert "ma5" in factors
    assert "ma10" in factors
    assert "ma20" in factors
    assert "ma60" in factors
    assert "volume_ratio" in factors
    assert "price_change" in factors
    assert "volatility" in factors


def test_list_by_category(registry):
    """测试按类别列出因子"""
    ma_factors = registry.list_by_category("ma")
    assert "ma5" in ma_factors
    assert "ma10" in ma_factors


def test_calculate_ma5(registry, sample_df):
    """测试计算 MA5"""
    result = registry.calculate("ma5", sample_df)
    assert len(result) == len(sample_df)
    # 前 4 个值应该是 NaN
    assert pd.isna(result.iloc[0])
    assert pd.isna(result.iloc[3])
    # 第 5 个值应该是前 5 个收盘价的平均值
    assert result.iloc[4] == pytest.approx(102.0)


def test_calculate_volume_ratio(registry, sample_df):
    """测试计算量比"""
    result = registry.calculate("volume_ratio", sample_df)
    assert len(result) == len(sample_df)


def test_calculate_price_change(registry, sample_df):
    """测试计算涨跌幅"""
    result = registry.calculate("price_change", sample_df)
    assert len(result) == len(sample_df)
    # 第一个值应该是 NaN
    assert pd.isna(result.iloc[0])
    # 第二个值应该是 (101-100)/100 = 0.01
    assert result.iloc[1] == pytest.approx(0.01)


def test_register_custom_factor():
    """测试注册自定义因子"""
    registry = FactorRegistry()

    def custom_factor(df):
        return df["close"] * 2

    registry.register("custom", custom_factor, "自定义因子", "custom")
    assert "custom" in registry.list_factors()

    sample_df = pd.DataFrame({"close": [100, 200]})
    result = registry.calculate("custom", sample_df)
    assert result.iloc[0] == 200
    assert result.iloc[1] == 400


def test_get_factor_not_found(registry):
    """测试获取不存在的因子"""
    with pytest.raises(ValueError):
        registry.get_factor("nonexistent")
