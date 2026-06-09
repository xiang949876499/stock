import pytest
from src.integrations.base import BaseAdapter
from src.integrations.registry import IntegrationRegistry


class MockAdapter(BaseAdapter):
    """测试用适配器"""

    async def initialize(self) -> bool:
        return True

    async def health_check(self) -> bool:
        return True


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
