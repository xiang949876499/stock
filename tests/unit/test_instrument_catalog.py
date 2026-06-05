"""标的目录测试"""

import pytest
from src.data.catalog.manager import InstrumentCatalog


@pytest.fixture
def catalog():
    """标的目录实例"""
    return InstrumentCatalog()


def test_qlib_to_vt(catalog):
    """测试 qlib 代码转 vt_symbol"""
    assert catalog.qlib_to_vt("SH600519") == "600519.SSE"
    assert catalog.qlib_to_vt("SZ000858") == "000858.SZE"
    assert catalog.qlib_to_vt("HK00700") == "00700.HK"


def test_vt_to_qlib(catalog):
    """测试 vt_symbol 转 qlib 代码"""
    assert catalog.vt_to_qlib("600519.SSE") == "SH600519"
    assert catalog.vt_to_qlib("000858.SZE") == "SZ000858"
    assert catalog.vt_to_qlib("00700.HK") == "HK00700"


def test_validate_vt_symbol(catalog):
    """测试验证 vt_symbol"""
    assert catalog.validate_vt_symbol("600519.SSE") is True
    assert catalog.validate_vt_symbol("000000.SSE") is False


def test_get_lot_size(catalog):
    """测试获取最小交易单位"""
    assert catalog.get_lot_size("600519.SSE") == 100
    assert catalog.get_lot_size("00700.HK") == 100
    assert catalog.get_lot_size("999999.SSE") == 100  # 默认值


def test_get_name(catalog):
    """测试获取股票名称"""
    assert catalog.get_name("600519") == "贵州茅台"
    assert catalog.get_name("000858") == "五粮液"


def test_add_instrument(catalog):
    """测试添加标的"""
    catalog.add_instrument("601318", {
        "vt_symbol": "601318.SSE",
        "name": "中国平安",
        "market": "A",
        "lot_size": 100,
    })
    assert catalog.validate_vt_symbol("601318.SSE") is True


def test_remove_instrument(catalog):
    """测试删除标的"""
    catalog.remove_instrument("600519")
    # 注意：这会从默认映射中删除
