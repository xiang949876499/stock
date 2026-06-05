"""回测 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.infra.logger import get_logger

logger = get_logger("backtest_api")

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    """回测请求"""
    symbols: list[str]
    strategy: str
    start_date: str
    end_date: str
    initial_capital: float = 1000000.0


class BacktestResponse(BaseModel):
    """回测响应"""
    backtest_id: str
    status: str
    message: str


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """运行回测"""
    try:
        # TODO: 实现回测
        import uuid
        backtest_id = str(uuid.uuid4())

        return BacktestResponse(
            backtest_id=backtest_id,
            status="pending",
            message="回测功能待实现",
        )
    except Exception as e:
        logger.error(f"运行回测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{backtest_id}")
async def get_backtest_result(backtest_id: str):
    """获取回测结果"""
    # TODO: 实现回测结果查询
    return {
        "backtest_id": backtest_id,
        "status": "pending",
        "message": "回测功能待实现",
    }


@router.get("/strategies")
async def list_backtest_strategies():
    """获取回测策略列表"""
    return [
        {"name": "ma_cross", "description": "均线金叉策略"},
        {"name": "macd", "description": "MACD 策略"},
        {"name": "trend", "description": "趋势跟踪策略"},
        {"name": "mean_reversion", "description": "均值回归策略"},
    ]
