"""消息推送基类"""

from abc import ABC, abstractmethod


class BasePusher(ABC):
    """消息推送基类"""

    @abstractmethod
    async def send(self, content: str) -> bool:
        """发送消息"""
        pass
