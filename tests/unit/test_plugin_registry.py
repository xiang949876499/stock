"""插件注册表测试"""

import pytest
from src.plugins.base import AnalysisPlugin
from src.plugins.registry import PluginRegistry


class MockPlugin(AnalysisPlugin):
    """模拟插件"""

    @property
    def name(self) -> str:
        return "mock_plugin"

    @property
    def description(self) -> str:
        return "A mock plugin for testing"

    async def execute(self, stock_data, params):
        return {"result": "mock"}

    def get_parameters(self):
        return {}


class MockPlugin2(AnalysisPlugin):
    """第二个模拟插件"""

    _custom_name: str = "mock_plugin_2"

    @property
    def name(self) -> str:
        return self._custom_name

    @property
    def description(self) -> str:
        return "Second mock plugin"

    async def execute(self, stock_data, params):
        return {"result": "mock2"}

    def get_parameters(self):
        return {}


@pytest.fixture(autouse=True)
def clear_registry():
    """每个测试前清空注册表"""
    PluginRegistry._plugins.clear()
    yield


def test_register_plugin():
    """测试注册插件"""
    plugin = MockPlugin()
    PluginRegistry.register(plugin)
    assert PluginRegistry.get("mock_plugin") == plugin


def test_get_nonexistent_plugin():
    """测试获取不存在的插件"""
    assert PluginRegistry.get("nonexistent") is None


def test_list_plugins():
    """测试列出插件"""
    plugin = MockPlugin()
    PluginRegistry.register(plugin)
    result = PluginRegistry.list_plugins()
    assert "mock_plugin" in result
    assert result["mock_plugin"] == "A mock plugin for testing"


def test_get_all_plugins():
    """测试获取所有插件"""
    plugin1 = MockPlugin()
    plugin2 = MockPlugin2()
    PluginRegistry.register(plugin1)
    PluginRegistry.register(plugin2)
    all_plugins = PluginRegistry.get_all()
    assert len(all_plugins) == 2
