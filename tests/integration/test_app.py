"""Application integration tests."""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Stock Hub API"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"healthy", "degraded"}
    assert "checks" in data


def test_health_reports_core_dependency_state(monkeypatch):
    class FakeScheduler:
        running = True

    class FakeSchedulerWrapper:
        scheduler = FakeScheduler()

    class FakeCursor:
        def fetchone(self):
            return (1,)

    class FakeDB:
        def execute(self, sql):
            assert sql == "SELECT 1"
            return FakeCursor()

    class FakeEngine:
        db = FakeDB()

        def is_running(self):
            return True

    monkeypatch.setattr("src.main.scheduler", FakeSchedulerWrapper())
    monkeypatch.setattr("src.main.trading_scheduler", FakeSchedulerWrapper())
    monkeypatch.setattr("src.web.api.trading.get_engine", lambda: FakeEngine())

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "checks": {
            "database": "healthy",
            "scheduler": "running",
            "trading_scheduler": "running",
            "trading_engine": "running",
        },
    }
