from typing import Optional
from src.integrations.base import BaseAdapter
from src.infra.logger import get_logger

logger = get_logger("integration_registry")


class IntegrationRegistry:
    """集成注册中心"""

    _instance: Optional["IntegrationRegistry"] = None
    _adapters: dict[str, BaseAdapter] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def clear(cls):
        """清空注册中心（用于测试）"""
        if cls._instance is not None:
            cls._instance._adapters.clear()
        cls._instance = None

    def register(self, adapter: BaseAdapter):
        """注册适配器"""
        self._adapters[adapter.name] = adapter
        logger.info(f"注册集成适配器: {adapter.name}")

    def get(self, name: str) -> Optional[BaseAdapter]:
        """获取适配器"""
        return self._adapters.get(name)

    def list_available(self) -> list[str]:
        """列出可用适配器"""
        return [name for name, adapter in self._adapters.items() if adapter.is_available()]

    async def initialize_all(self):
        """初始化所有已启用的适配器"""
        for name, adapter in self._adapters.items():
            if adapter.is_available():
                try:
                    success = await adapter.initialize()
                    if success:
                        logger.info(f"适配器 {name} 初始化成功")
                    else:
                        logger.warning(f"适配器 {name} 初始化失败")
                except Exception as e:
                    logger.error(f"适配器 {name} 初始化异常: {e}")

    async def health_check_all(self) -> dict[str, bool]:
        """检查所有适配器健康状态"""
        results = {}
        for name, adapter in self._adapters.items():
            if adapter.is_available():
                try:
                    results[name] = await adapter.health_check()
                except Exception as e:
                    logger.error(f"适配器 {name} 健康检查异常: {e}")
                    results[name] = False
            else:
                results[name] = False
        return results


# 全局注册中心
registry = IntegrationRegistry()
