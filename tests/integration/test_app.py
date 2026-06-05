"""应用集成测试"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    """测试客户端"""
    return TestClient(app)


def test_root(client):
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Stock Hub API"
    assert data["version"] == "0.1.0"
    assert data["status"] == "running"


def test_health(client):
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
