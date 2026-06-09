import pytest
from src.integrations.quantaxis.adapter import QUANTAXISAdapter


def test_adapter_creation():
    """测试适配器创建"""
    adapter = QUANTAXISAdapter(enabled=False)
    assert adapter.name == "quantaxis"
    assert adapter.is_available() is False


def test_adapter_list_data_types():
    """测试列出数据类型"""
    adapter = QUANTAXISAdapter(enabled=False)
    types = adapter.list_data_types()
    assert "day" in types
    assert "min" in types
    assert "tick" in types
