"""插件 API"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.plugins.registry import PluginRegistry
from src.plugins.export import ResultExporter

router = APIRouter(prefix="/plugins", tags=["plugins"])


class PluginExecuteRequest(BaseModel):
    """插件执行请求"""
    symbol: str
    params: Dict[str, Any] = {}
    period: Optional[str] = None


class AgentRunRequest(BaseModel):
    """代理运行请求"""
    query: str
    context: Dict[str, Any] = {}


@router.get("/")
async def list_plugins():
    """列出所有可用插件"""
    return PluginRegistry.list_plugins()


@router.get("/{plugin_name}")
async def get_plugin_info(plugin_name: str):
    """获取插件信息"""
    plugin = PluginRegistry.get(plugin_name)
    if not plugin:
        raise HTTPException(404, f"Plugin {plugin_name} not found")
    return {
        "name": plugin.name,
        "description": plugin.description,
        "version": plugin.version,
        "parameters": plugin.get_parameters()
    }


@router.post("/{plugin_name}/execute")
async def execute_plugin(
    plugin_name: str,
    request: PluginExecuteRequest
):
    """执行插件分析"""
    plugin = PluginRegistry.get(plugin_name)
    if not plugin:
        raise HTTPException(404, f"Plugin {plugin_name} not found")

    stock_data = {
        "symbol": request.symbol,
        "current_price": 100.0,
    }

    result = await plugin.execute(
        stock_data=stock_data,
        params=request.params
    )
    return result


@router.get("/{plugin_name}/export")
async def export_plugin_result(
    plugin_name: str,
    symbol: str,
    format: str = "json"
):
    """导出插件分析结果"""
    plugin = PluginRegistry.get(plugin_name)
    if not plugin:
        raise HTTPException(404, f"Plugin {plugin_name} not found")

    # 执行分析
    stock_data = {"symbol": symbol, "current_price": 100.0}
    result = await plugin.execute(stock_data=stock_data, params={})

    # 导出
    if format == "json":
        content = ResultExporter.to_json(result)
        media_type = "application/json"
    elif format == "csv":
        content = ResultExporter.to_csv(result)
        media_type = "text/csv"
    else:
        raise HTTPException(400, f"Unsupported format: {format}")

    filename = ResultExporter.get_export_filename(plugin_name, symbol, format)

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.post("/agents/{agent_name}/run")
async def run_agent(
    agent_name: str,
    request: AgentRunRequest
):
    """运行分析代理"""
    from src.plugins.agents.registry import AgentRegistry

    agent = AgentRegistry.get(agent_name)
    if not agent:
        raise HTTPException(404, f"Agent {agent_name} not found")

    result = await agent.run(
        query=request.query,
        context=request.context
    )
    return {"result": result}
