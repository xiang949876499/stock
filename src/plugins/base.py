"""插件基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class AnalysisPlugin(ABC):
    """分析插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass

    @property
    def version(self) -> str:
        """插件版本"""
        return "1.0.0"

    @abstractmethod
    async def execute(
        self,
        stock_data: Any,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行分析

        Args:
            stock_data: 股票数据
            params: 分析参数

        Returns:
            分析结果字典
        """
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义

        Returns:
            参数定义字典，格式:
            {
                "param_name": {
                    "type": "int|float|str|List[str]",
                    "default": ...,
                    "description": "..."
                }
            }
        """
        pass
