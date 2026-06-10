# src/trading_rules/api.py
"""交易准则 API"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional

from .service import TradingRuleService
from .models import RuleCategory

router = APIRouter(prefix="/rules", tags=["rules"])

# 服务实例（延迟初始化）
_service: Optional[TradingRuleService] = None


def get_service() -> TradingRuleService:
    """获取服务实例"""
    global _service
    if _service is None:
        _service = TradingRuleService()
    return _service


class CheckRequest(BaseModel):
    """检查请求"""
    symbol: str
    market: str = "A"
    scenario: str = "entry"
    stock_data: dict = {}


@router.get("/")
async def list_rules():
    """获取所有准则"""
    service = get_service()
    rules = service.get_all_rules()
    return {
        "total": len(rules),
        "rules": [r.model_dump() for r in rules]
    }


@router.get("/{rule_id}")
async def get_rule(rule_id: str):
    """获取单条准则"""
    service = get_service()
    rule = service.get_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="准则不存在")
    return rule.model_dump()


@router.get("/category/{category}")
async def get_rules_by_category(category: str):
    """按类别获取准则"""
    service = get_service()
    rules = service.get_rules_by_category(category)
    return {
        "category": category,
        "total": len(rules),
        "rules": [r.model_dump() for r in rules]
    }


@router.get("/search")
async def search_rules(q: str = Query(..., description="搜索关键词")):
    """搜索准则"""
    service = get_service()
    rules = service.search_rules(q)
    return {
        "keyword": q,
        "total": len(rules),
        "rules": [r.model_dump() for r in rules]
    }


@router.post("/check")
async def check_rules(request: CheckRequest):
    """检查准则"""
    service = get_service()
    result = service.check_stock(
        symbol=request.symbol,
        market=request.market,
        scenario=request.scenario,
        stock_data=request.stock_data
    )
    return result


@router.get("/statistics")
async def get_statistics():
    """获取准则统计"""
    service = get_service()
    return service.get_statistics()
