"""事件总线测试"""

import pytest
import asyncio
from src.infra.event_bus import EventBus, EventType, Event


@pytest.fixture
def event_bus():
    """事件总线实例"""
    return EventBus()


def test_event_bus_subscribe(event_bus):
    """测试订阅事件"""
    handler = lambda event: None
    event_bus.on(EventType.DATA_UPDATE, handler)
    assert handler in event_bus._handlers[EventType.DATA_UPDATE]


def test_event_bus_unsubscribe(event_bus):
    """测试取消订阅"""
    handler = lambda event: None
    event_bus.on(EventType.DATA_UPDATE, handler)
    event_bus.off(EventType.DATA_UPDATE, handler)
    assert handler not in event_bus._handlers[EventType.DATA_UPDATE]


@pytest.mark.asyncio
async def test_event_bus_emit(event_bus):
    """测试发布事件"""
    received_events = []

    async def handler(event):
        received_events.append(event)

    event_bus.on(EventType.DATA_UPDATE, handler)

    event = Event(type=EventType.DATA_UPDATE, data={"symbol": "600519"})
    await event_bus.emit(event)

    assert len(received_events) == 1
    assert received_events[0].data == {"symbol": "600519"}


@pytest.mark.asyncio
async def test_event_bus_emit_multiple_handlers(event_bus):
    """测试多个处理器"""
    received_events = []

    async def handler1(event):
        received_events.append(("handler1", event))

    async def handler2(event):
        received_events.append(("handler2", event))

    event_bus.on(EventType.DATA_UPDATE, handler1)
    event_bus.on(EventType.DATA_UPDATE, handler2)

    event = Event(type=EventType.DATA_UPDATE, data={"symbol": "600519"})
    await event_bus.emit(event)

    assert len(received_events) == 2


def test_event_bus_emit_sync(event_bus):
    """测试同步发布事件"""
    received_events = []

    def handler(event):
        received_events.append(event)

    event_bus.on(EventType.DATA_UPDATE, handler)

    event = Event(type=EventType.DATA_UPDATE, data={"symbol": "600519"})
    event_bus.emit_sync(event)

    assert len(received_events) == 1
