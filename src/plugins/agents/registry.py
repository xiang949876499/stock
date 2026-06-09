"""代理注册表"""

from typing import Dict, List, Optional, Type

from .base import AnalysisAgent


class AgentRegistry:
    """代理注册表"""

    _agents: Dict[str, Type[AnalysisAgent]] = {}

    @classmethod
    def register(cls, name: str, agent_cls: Type[AnalysisAgent]) -> None:
        """注册代理

        Args:
            name: 代理名称
            agent_cls: 代理类
        """
        cls._agents[name] = agent_cls

    @classmethod
    def get(cls, name: str) -> Optional[Type[AnalysisAgent]]:
        """获取代理类

        Args:
            name: 代理名称

        Returns:
            代理类，不存在返回 None
        """
        return cls._agents.get(name)

    @classmethod
    def list_agents(cls) -> Dict[str, str]:
        """列出所有已注册代理

        Returns:
            {代理名称: 代理类名} 字典
        """
        return {name: cls_.__name__ for name, cls_ in cls._agents.items()}

    @classmethod
    def get_all(cls) -> List[Type[AnalysisAgent]]:
        """获取所有代理类

        Returns:
            代理类列表
        """
        return list(cls._agents.values())

    @classmethod
    def clear(cls) -> None:
        """清空注册表（用于测试）"""
        cls._agents.clear()
