"""连接器注册表"""

from typing import Dict, Any, List, Optional
from src.data.connectors.base import DataConnector
from src.infra.logger import get_logger

logger = get_logger("connector_registry")


class ConnectorRegistry:
    """连接器注册表"""

    _connectors: Dict[str, DataConnector] = {}

    @classmethod
    def register(cls, connector: DataConnector) -> None:
        """注册连接器

        Args:
            connector: 连接器实例
        """
        cls._connectors[connector.name] = connector
        logger.info(f"注册数据连接器: {connector.name}")

    @classmethod
    def get(cls, name: str) -> Optional[DataConnector]:
        """获取连接器

        Args:
            name: 连接器名称

        Returns:
            连接器实例，不存在返回 None
        """
        return cls._connectors.get(name)

    @classmethod
    def get_by_capability(cls, capability: str) -> List[DataConnector]:
        """根据能力获取连接器

        Args:
            capability: 数据类型能力

        Returns:
            支持该能力的连接器列表
        """
        return [
            c for c in cls._connectors.values()
            if capability in c.capabilities
        ]

    @classmethod
    def list_connectors(cls) -> Dict[str, List[str]]:
        """列出所有连接器

        Returns:
            {连接器名称: 能力列表} 字典
        """
        return {
            name: c.capabilities
            for name, c in cls._connectors.items()
        }

    @classmethod
    def clear(cls) -> None:
        """清空注册表（用于测试）"""
        cls._connectors.clear()
