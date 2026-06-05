"""Agent 契约 v1"""

from pydantic import BaseModel


class AgentTool(BaseModel):
    """Agent 工具契约"""
    name: str
    description: str
    parameters: dict


# Agent 工具集
AGENT_TOOLS = [
    AgentTool(
        name="get_stock_price",
        description="获取股票实时价格",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "股票代码"},
                "market": {"type": "string", "enum": ["A", "HK"]}
            },
            "required": ["symbol", "market"]
        }
    ),
    AgentTool(
        name="get_kline",
        description="获取 K 线数据",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "market": {"type": "string"},
                "period": {"type": "string", "enum": ["daily", "weekly", "monthly"]},
                "days": {"type": "integer", "default": 30}
            },
            "required": ["symbol", "market"]
        }
    ),
    AgentTool(
        name="get_technical_indicators",
        description="获取技术指标",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "market": {"type": "string"}
            },
            "required": ["symbol", "market"]
        }
    ),
    AgentTool(
        name="get_news",
        description="获取最新新闻",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "market": {"type": "string"},
                "days": {"type": "integer", "default": 7}
            },
            "required": ["symbol", "market"]
        }
    ),
    AgentTool(
        name="analyze_stock",
        description="分析股票",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "market": {"type": "string"},
                "strategy": {"type": "string"}
            },
            "required": ["symbol", "market"]
        }
    ),
]
