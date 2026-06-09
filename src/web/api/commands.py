"""命令 API"""

from fastapi import APIRouter
from typing import List, Dict

router = APIRouter(prefix="/commands", tags=["commands"])

COMMANDS = [
    {"name": "dcf", "description": "DCF 估值分析", "plugin": "dcf_valuation", "usage": "/dcf <股票代码>"},
    {"name": "comps", "description": "可比公司分析", "plugin": "comparable_analysis", "usage": "/comps <股票代码> <同行代码>"},
    {"name": "screen", "description": "股票筛选", "plugin": "stock_screening", "usage": "/screen <筛选条件>"},
    {"name": "earnings", "description": "财报分析", "plugin": "earnings_analysis", "usage": "/earnings <股票代码> <期间>"},
]


@router.get("/")
async def list_commands() -> List[Dict]:
    """列出所有可用命令"""
    return COMMANDS
