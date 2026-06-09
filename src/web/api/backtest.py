"""回测 API"""

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional
import uuid

from src.exceptions import ValidationError
from src.infra.logger import get_logger
from src.web.deps import get_backtrader_adapter
from src.integrations.backtrader.adapter import BacktraderAdapter

logger = get_logger("backtest_api")

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    """回测请求"""
    symbols: list[str] = Field(..., min_length=1, max_length=100, description="股票代码列表")
    strategy: str = Field(..., description="策略名称")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="开始日期")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="结束日期")
    initial_capital: float = Field(1000000.0, gt=0, description="初始资金")
    params: Optional[dict] = Field(None, description="策略参数")


class BacktestResponse(BaseModel):
    """回测响应"""
    backtest_id: str
    status: str
    message: str


class BacktestResultResponse(BaseModel):
    """回测结果响应"""
    backtest_id: str
    strategy_name: str
    symbols: list[str]
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    adapter: BacktraderAdapter = Depends(get_backtrader_adapter),
):
    """运行回测"""
    try:
        backtest_id = str(uuid.uuid4())

        # 检查策略是否存在
        available_strategies = adapter.list_strategies()
        if request.strategy not in available_strategies:
            raise ValidationError(f"未知策略: {request.strategy}，可用策略: {available_strategies}")

        # 运行回测
        result = await adapter.run_backtest(
            backtest_id=backtest_id,
            strategy_name=request.strategy,
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            params=request.params,
        )

        return BacktestResponse(
            backtest_id=backtest_id,
            status="completed",
            message=f"回测完成，收益率: {result.total_return:.2%}",
        )
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"运行回测失败: {e}")
        raise ValidationError(f"运行回测失败: {e}")


@router.get("/results/{backtest_id}")
async def get_backtest_result(backtest_id: str):
    """获取回测结果"""
    # TODO: 从数据库获取回测结果
    return {
        "backtest_id": backtest_id,
        "status": "pending",
        "message": "回测结果查询待实现",
    }


@router.get("/strategies")
async def list_backtest_strategies(
    adapter: BacktraderAdapter = Depends(get_backtrader_adapter),
):
    """获取回测策略列表"""
    strategies = adapter.list_strategies()
    return [{"name": s, "description": f"{s} 策略"} for s in strategies]
