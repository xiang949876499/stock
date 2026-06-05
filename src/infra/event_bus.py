"""事件总线"""

from typing import Callable, Any
from collections import defaultdict
from datetime import datetime
from enum import Enum
import asyncio


class EventType(str, Enum):
    """事件类型"""
    DATA_UPDATE = "data.update"
    SIGNAL_GENERATED = "signal.generated"
    SIGNAL_APPROVED = "signal.approved"
    ORDER_SENT = "order.sent"
    ORDER_FILLED = "order.filled"
    TRADE_EXECUTED = "trade.executed"
    SYSTEM_ERROR = "system.error"


class Event:
    """事件"""

    def __init__(self, type: EventType, data: Any):
        self.type = type
        self.data = data
        self.timestamp = datetime.now()


class EventBus:
    """事件总线"""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event_type: EventType, handler: Callable):
        """订阅事件"""
        self._handlers[event_type].append(handler)

    def off(self, event_type: EventType, handler: Callable):
        """取消订阅"""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def emit(self, event: Event):
        """发布事件（异步）"""
        handlers = self._handlers.get(event.type, [])
        tasks = [handler(event) for handler in handlers]
        await asyncio.gather(*tasks, return_exceptions=True)

    def emit_sync(self, event: Event):
        """发布事件（同步）"""
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"事件处理失败: {e}")
