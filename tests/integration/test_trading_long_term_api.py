"""Long-term simulated trading report API tests."""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from src.infra.database import Database
from src.main import app
from src.trading.engine import SimulationEngine
from src.web.api.trading import get_engine


class _TestDatabase(Database):
    def connect(self):
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row


@pytest.fixture
def client(tmp_path):
    db = _TestDatabase(str(tmp_path / "test_long_term_reports.db"))
    db.connect()
    db.init_sim_tables()
    engine = SimulationEngine(db)

    app.dependency_overrides[get_engine] = lambda: engine
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_engine, None)
    db.disconnect()


def test_get_long_term_reports(client):
    response = client.get("/api/v1/trading/long-term-reports")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
