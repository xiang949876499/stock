from abc import ABC, abstractmethod
from typing import Optional
from src.infra.logger import get_logger

logger = get_logger("integration_base")


class BaseAdapter(ABC):
    """集成适配器基类"""

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.logger = get_logger(f"adapter_{name}")

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化适配器，返回是否成功"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass

    def is_available(self) -> bool:
        """检查适配器是否可用"""
        return self.enabled
