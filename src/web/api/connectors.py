"""连接器 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.data.connectors.registry import ConnectorRegistry

router = APIRouter(prefix="/connectors", tags=["connectors"])


class ConnectorFetchRequest(BaseModel):
    """连接器数据获取请求"""
    type: str = "quote"
    symbol: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    period: Optional[str] = None
    interval: Optional[str] = None


@router.get("/")
async def list_connectors():
    """列出所有可用连接器"""
    return ConnectorRegistry.list_connectors()


@router.get("/{connector_name}")
async def get_connector_info(connector_name: str):
    """获取连接器信息"""
    connector = ConnectorRegistry.get(connector_name)
    if not connector:
        raise HTTPException(404, f"Connector {connector_name} not found")
    return {
        "name": connector.name,
        "capabilities": connector.capabilities,
    }


@router.get("/{connector_name}/health")
async def check_connector_health(connector_name: str):
    """检查连接器健康状态"""
    connector = ConnectorRegistry.get(connector_name)
    if not connector:
        raise HTTPException(404, f"Connector {connector_name} not found")
    healthy = await connector.health_check()
    return {
        "name": connector.name,
        "healthy": healthy,
    }


@router.post("/{connector_name}/fetch")
async def fetch_data(
    connector_name: str,
    request: ConnectorFetchRequest
):
    """从连接器获取数据"""
    connector = ConnectorRegistry.get(connector_name)
    if not connector:
        raise HTTPException(404, f"Connector {connector_name} not found")

    query = {
        "type": request.type,
        "symbol": request.symbol,
    }
    if request.start_date:
        query["start_date"] = request.start_date
    if request.end_date:
        query["end_date"] = request.end_date
    if request.period:
        query["period"] = request.period
    if request.interval:
        query["interval"] = request.interval

    result = await connector.fetch(query)

    if not result.get("success", False):
        raise HTTPException(500, result.get("error", "Unknown error"))

    return result


@router.post("/{connector_name}/connect")
async def connect_connector(connector_name: str):
    """初始化连接器连接"""
    connector = ConnectorRegistry.get(connector_name)
    if not connector:
        raise HTTPException(404, f"Connector {connector_name} not found")

    success = await connector.connect({})
    return {
        "name": connector.name,
        "connected": success,
    }


@router.post("/{connector_name}/disconnect")
async def disconnect_connector(connector_name: str):
    """断开连接器"""
    connector = ConnectorRegistry.get(connector_name)
    if not connector:
        raise HTTPException(404, f"Connector {connector_name} not found")

    await connector.disconnect()
    return {
        "name": connector.name,
        "connected": False,
    }
