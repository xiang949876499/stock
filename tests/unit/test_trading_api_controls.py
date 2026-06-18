import asyncio

import pytest

from src.web.api import trading


class FakeEngine:
    def __init__(self):
        self.started = False
        self.stopped = False
        self.analysis_requested = False

    def start(self):
        self.started = True
        self.stopped = False

    def stop(self):
        self.stopped = True
        self.started = False

    def is_running(self):
        return self.started

    async def run_analysis_cycle(self):
        self.analysis_requested = True


class FakeTask:
    def __init__(self, coro):
        self.coro = coro
        self.cancelled = False

    def done(self):
        return False

    def cancel(self):
        self.cancelled = True
        self.coro.close()

    def add_done_callback(self, callback):
        self.callback = callback


@pytest.fixture(autouse=True)
def clear_initial_analysis_task():
    trading._initial_analysis_task = None
    yield
    task = trading._initial_analysis_task
    if task and hasattr(task, "cancel") and not task.done():
        task.cancel()
    trading._initial_analysis_task = None


@pytest.mark.asyncio
async def test_start_trading_schedules_first_analysis(monkeypatch):
    engine = FakeEngine()
    scheduled = {}

    def capture_create_task(coro):
        scheduled["task"] = FakeTask(coro)
        return scheduled["task"]

    monkeypatch.setattr(asyncio, "create_task", capture_create_task)

    response = await trading.start_trading(engine)

    assert response == {"status": "running", "analysis": "scheduled"}
    assert engine.started is True
    assert isinstance(scheduled["task"], FakeTask)
    assert trading._initial_analysis_task is scheduled["task"]

    await scheduled["task"].coro

    assert engine.analysis_requested is True


@pytest.mark.asyncio
async def test_stop_trading_cancels_pending_initial_analysis(monkeypatch):
    engine = FakeEngine()
    scheduled = {}

    def capture_create_task(coro):
        scheduled["task"] = FakeTask(coro)
        return scheduled["task"]

    monkeypatch.setattr(asyncio, "create_task", capture_create_task)

    await trading.start_trading(engine)
    response = await trading.stop_trading(engine)

    assert response == {"status": "stopped"}
    assert engine.stopped is True
    assert scheduled["task"].cancelled is True
    assert trading._initial_analysis_task is None
