"""数据连接器基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class DataConnector(ABC):
    """数据连接器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """连接器名称"""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """支持的数据类型"""
        pass

    @abstractmethod
    async def connect(self, config: Dict[str, Any]) -> bool:
        """建立连接

        Args:
            config: 连接配置

        Returns:
            是否连接成功
        """
        pass

    @abstractmethod
    async def fetch(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """获取数据

        Args:
            query: 查询参数，格式:
                {
                    "type": "quote|kline|financial",
                    "symbol": "0700",
                    ...
                }

        Returns:
            数据字典
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass

    async def health_check(self) -> bool:
        """健康检查"""
        return True
