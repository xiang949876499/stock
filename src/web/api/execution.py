"""执行 API"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from src.execution.service import ExecutionService
from src.web.deps import get_execution_service
from src.exceptions import DataProviderError
from src.infra.logger import get_logger

logger = get_logger("execution_api")

router = APIRouter(prefix="/execution", tags=["execution"])


@router.get("/positions")
async def get_positions(
    service: ExecutionService = Depends(get_execution_service),
):
    """获取持仓"""
    try:
        positions = await service.get_positions()
        return list(positions.values()) if positions else []
    except Exception as e:
        logger.error(f"获取持仓失败: {e}")
        raise DataProviderError(f"获取持仓失败: {e}")


@router.get("/account")
async def get_account(
    service: ExecutionService = Depends(get_execution_service),
):
    """获取账户"""
    try:
        account = await service.get_account()
        if account:
            return account
        return {"balance": 0, "available": 0, "frozen": 0}
    except Exception as e:
        logger.error(f"获取账户失败: {e}")
        raise DataProviderError(f"获取账户失败: {e}")


@router.get("/orders")
async def list_orders(
    symbol: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """获取订单列表"""
    # TODO: 实现订单列表
    return []


@router.get("/pnl")
async def get_pnl(
    service: ExecutionService = Depends(get_execution_service),
):
    """获取盈亏"""
    try:
        pnl = await service.calculate_pnl()
        return {"pnl": pnl}
    except Exception as e:
        logger.error(f"获取盈亏失败: {e}")
        raise DataProviderError(f"获取盈亏失败: {e}")
