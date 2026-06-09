"""插件 API 集成测试"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_plugins(client):
    """测试列出插件"""
    response = client.get("/api/v1/plugins/")
    assert response.status_code == 200
    data = response.json()
    assert "dcf_valuation" in data
    assert "comparable_analysis" in data
    assert "stock_screening" in data
    assert "earnings_analysis" in data


def test_get_plugin_info(client):
    """测试获取插件信息"""
    response = client.get("/api/v1/plugins/dcf_valuation")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "dcf_valuation"
    assert "parameters" in data
    assert "years" in data["parameters"]
    assert "growth_rate" in data["parameters"]


def test_get_plugin_info_not_found(client):
    """测试获取不存在的插件信息返回 404"""
    response = client.get("/api/v1/plugins/nonexistent_plugin")
    assert response.status_code == 404


def test_execute_dcf_plugin(client):
    """测试执行 DCF 插件"""
    response = client.post(
        "/api/v1/plugins/dcf_valuation/execute",
        json={
            "symbol": "600519",
            "params": {
                "years": 5,
                "growth_rate": 0.15
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "enterprise_value" in data
    assert "per_share_value" in data
    assert "cash_flows" in data
    assert "terminal_value" in data
    assert isinstance(data["cash_flows"], list)
    assert len(data["cash_flows"]) == 5


def test_execute_comparable_analysis_plugin(client):
    """测试执行可比公司分析插件"""
    response = client.post(
        "/api/v1/plugins/comparable_analysis/execute",
        json={
            "symbol": "600519",
            "params": {
                "peer_codes": ["000858", "002304"],
                "metrics": ["PE", "PB"]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "peer_comparison" in data
    assert "avg_peer_metrics" in data
    assert len(data["peer_comparison"]) == 2


def test_execute_screening_plugin(client):
    """测试执行股票筛选插件"""
    response = client.post(
        "/api/v1/plugins/stock_screening/execute",
        json={
            "symbol": "600519",
            "params": {
                "universe": "hs300",
                "limit": 5
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total_count" in data
    assert len(data["results"]) <= 5


def test_execute_earnings_plugin(client):
    """测试执行财报分析插件"""
    response = client.post(
        "/api/v1/plugins/earnings_analysis/execute",
        json={
            "symbol": "600519",
            "params": {
                "period": "2024Q3"
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "highlights" in data
    assert "risks" in data
    assert "financial_metrics" in data


def test_execute_plugin_not_found(client):
    """测试执行不存在的插件返回 404"""
    response = client.post(
        "/api/v1/plugins/nonexistent_plugin/execute",
        json={
            "symbol": "600519",
            "params": {}
        }
    )
    assert response.status_code == 404


def test_list_commands(client):
    """测试列出命令"""
    response = client.get("/api/v1/commands/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == "dcf"
    assert "usage" in data[0]
    # 验证所有预期命令存在
    command_names = [cmd["name"] for cmd in data]
    assert "dcf" in command_names
    assert "comps" in command_names
    assert "screen" in command_names
    assert "earnings" in command_names
