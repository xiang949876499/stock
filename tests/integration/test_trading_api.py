"""交易 API 集成测试"""

import sqlite3

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.web.api.trading import get_engine
from src.trading.engine import SimulationEngine
from src.infra.database import Database


class _TestDatabase(Database):
    """允许跨线程访问的测试数据库"""

    def connect(self):
        """连接数据库（允许跨线程使用）"""
        self.conn = sqlite3.connect(
            str(self.db_path), check_same_thread=False
        )
        self.conn.row_factory = sqlite3.Row


@pytest.fixture
def client(tmp_path):
    """使用临时数据库的测试客户端，确保测试隔离"""
    db_path = str(tmp_path / "test_sim_trading.db")
    db = _TestDatabase(db_path)
    db.connect()
    db.init_sim_tables()
    engine = SimulationEngine(db)

    def override_get_engine():
        return engine

    app.dependency_overrides[get_engine] = override_get_engine
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_engine, None)
    db.disconnect()


def test_get_account(client):
    """测试获取模拟账户"""
    response = client.get("/api/v1/trading/account")
    assert response.status_code == 200
    data = response.json()
    assert "account_id" in data
    assert "balance" in data


def test_get_positions(client):
    """测试获取持仓列表"""
    response = client.get("/api/v1/trading/positions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_trades(client):
    """测试获取交易记录"""
    response = client.get("/api/v1/trading/trades")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_start_stop(client):
    """测试启动和停止交易引擎"""
    # 启动引擎
    response = client.post("/api/v1/trading/start")
    assert response.status_code == 200
    assert response.json()["status"] == "running"

    # 验证状态为运行中
    response = client.get("/api/v1/trading/status")
    assert response.status_code == 200
    assert response.json()["running"] is True

    # 停止引擎
    response = client.post("/api/v1/trading/stop")
    assert response.status_code == 200
    assert response.json()["status"] == "stopped"

    # 验证状态为已停止
    response = client.get("/api/v1/trading/status")
    assert response.status_code == 200
    assert response.json()["running"] is False


def test_reset_account(client):
    """测试重置模拟账户"""
    response = client.post(
        "/api/v1/trading/account/reset",
        json={"initial_capital": 500000},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["initial_capital"] == 500000
    assert data["balance"] == 500000


def test_get_reports(client):
    """测试获取每日报告"""
    response = client.get("/api/v1/trading/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_analysis_logs(client):
    """测试获取分析日志"""
    response = client.get("/api/v1/trading/analysis-logs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_status(client):
    """测试获取引擎状态返回完整结构"""
    response = client.get("/api/v1/trading/status")
    assert response.status_code == 200
    data = response.json()
    assert "running" in data
    assert "account" in data
    assert "positions" in data
    assert isinstance(data["positions"], list)
