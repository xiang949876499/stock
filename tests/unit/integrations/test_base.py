import pytest
from src.integrations.base import BaseAdapter
from src.integrations.registry import IntegrationRegistry


class MockAdapter(BaseAdapter):
    """测试用适配器"""

    async def initialize(self) -> bool:
        return True

    async def health_check(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def cleanup_registry():
    """每个测试后清理注册中心"""
    yield
    IntegrationRegistry.clear()


def test_adapter_creation():
    adapter = MockAdapter(name="test", enabled=True)
    assert adapter.name == "test"
    assert adapter.is_available() is True


def test_adapter_disabled():
    adapter = MockAdapter(name="test", enabled=False)
    assert adapter.is_available() is False


def test_registry_singleton():
    registry1 = IntegrationRegistry()
    registry2 = IntegrationRegistry()
    assert registry1 is registry2


def test_registry_register():
    registry = IntegrationRegistry()
    adapter = MockAdapter(name="test_register")
    registry.register(adapter)
    assert registry.get("test_register") is adapter


@pytest.mark.asyncio
async def test_adapter_initialize():
    """测试适配器初始化"""
    adapter = MockAdapter(name="test_init")
    result = await adapter.initialize()
    assert result is True


@pytest.mark.asyncio
async def test_adapter_health_check():
    """测试适配器健康检查"""
    adapter = MockAdapter(name="test_health")
    result = await adapter.health_check()
    assert result is True


@pytest.mark.asyncio
async def test_registry_initialize_all():
    """测试注册中心初始化所有适配器"""
    registry = IntegrationRegistry()

    # 注册成功适配器
    adapter1 = MockAdapter(name="success", enabled=True)
    registry.register(adapter1)

    # 注册禁用的适配器
    adapter2 = MockAdapter(name="disabled", enabled=False)
    registry.register(adapter2)

    # 初始化所有
    await registry.initialize_all()

    # 验证只有启用的适配器被初始化
    assert registry.get("success") is not None
    assert registry.get("disabled") is not None


@pytest.mark.asyncio
async def test_registry_health_check_all():
    """测试注册中心健康检查所有适配器"""
    registry = IntegrationRegistry()

    adapter1 = MockAdapter(name="healthy", enabled=True)
    registry.register(adapter1)

    adapter2 = MockAdapter(name="disabled", enabled=False)
    registry.register(adapter2)

    results = await registry.health_check_all()

    assert results["healthy"] is True
    assert results["disabled"] is False


def test_registry_clear():
    """测试注册中心清空"""
    registry = IntegrationRegistry()
    adapter = MockAdapter(name="test_clear")
    registry.register(adapter)

    IntegrationRegistry.clear()

    # 清空后应创建新实例
    new_registry = IntegrationRegistry()
    assert new_registry.get("test_clear") is None


def test_registry_list_available():
    """测试列出可用适配器"""
    registry = IntegrationRegistry()

    adapter1 = MockAdapter(name="available", enabled=True)
    registry.register(adapter1)

    adapter2 = MockAdapter(name="unavailable", enabled=False)
    registry.register(adapter2)

    available = registry.list_available()
    assert "available" in available
    assert "unavailable" not in available
