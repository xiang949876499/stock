"""回测 API"""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field
from typing import Optional
import uuid

from src.exceptions import ValidationError
from src.infra.logger import get_logger

logger = get_logger("backtest_api")

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    """回测请求"""
    symbols: list[str] = Field(..., min_length=1, max_length=100, description="股票代码列表")
    strategy: str = Field(..., description="策略名称")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="开始日期")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="结束日期")
    initial_capital: float = Field(1000000.0, gt=0, description="初始资金")


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
        backtest_id = str(uuid.uuid4())

        return BacktestResponse(
            backtest_id=backtest_id,
            status="pending",
            message="回测功能待实现",
        )
    except Exception as e:
        logger.error(f"运行回测失败: {e}")
        raise ValidationError(f"运行回测失败: {e}")


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
