"""执行 API"""

from fastapi import APIRouter, HTTPException
from typing import Optional

from src.execution.service import ExecutionService
from src.infra.logger import get_logger

logger = get_logger("execution_api")

router = APIRouter(prefix="/execution", tags=["execution"])

# 执行服务实例（延迟初始化）
_execution_service: Optional[ExecutionService] = None


def get_execution_service() -> ExecutionService:
    """获取执行服务"""
    global _execution_service
    if _execution_service is None:
        _execution_service = ExecutionService()
    return _execution_service


@router.get("/positions")
async def get_positions():
    """获取持仓"""
    try:
        service = get_execution_service()
        positions = await service.get_positions()
        return list(positions.values()) if positions else []
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/account")
async def get_account():
    """获取账户"""
    try:
        service = get_execution_service()
        account = await service.get_account()
        if account:
            return account
        return {"balance": 0, "available": 0, "frozen": 0}
    except Exception as e:
        logger.error(f"获取账户失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orders")
async def list_orders(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
):
    """获取订单列表"""
    # TODO: 实现订单列表
    return []


@router.get("/pnl")
async def get_pnl():
    """获取盈亏"""
    try:
        service = get_execution_service()
        pnl = await service.calculate_pnl()
        return {"pnl": pnl}
    except Exception as e:
        logger.error(f"获取盈亏失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
