"""插件注册表"""

from typing import Dict, Any, Optional, List
from src.plugins.base import AnalysisPlugin


class PluginRegistry:
    """插件注册表"""

    _plugins: Dict[str, AnalysisPlugin] = {}

    @classmethod
    def register(cls, plugin: AnalysisPlugin) -> None:
        """注册插件

        Args:
            plugin: 插件实例
        """
        cls._plugins[plugin.name] = plugin

    @classmethod
    def get(cls, name: str) -> Optional[AnalysisPlugin]:
        """获取插件

        Args:
            name: 插件名称

        Returns:
            插件实例，不存在返回 None
        """
        return cls._plugins.get(name)

    @classmethod
    def list_plugins(cls) -> Dict[str, str]:
        """列出所有插件

        Returns:
            {插件名称: 插件描述} 字典
        """
        return {name: p.description for name, p in cls._plugins.items()}

    @classmethod
    def get_all(cls) -> List[AnalysisPlugin]:
        """获取所有插件

        Returns:
            插件实例列表
        """
        return list(cls._plugins.values())

    @classmethod
    def clear(cls) -> None:
        """清空注册表（用于测试）"""
        cls._plugins.clear()
