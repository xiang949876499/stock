"""分析 API"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional

from src.analysis.service import AnalysisService
from src.web.deps import get_analysis_service
from src.exceptions import AIProviderError
from src.infra.logger import get_logger

logger = get_logger("analysis_api")

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisRequest(BaseModel):
    """分析请求"""
    symbol: str = Field(..., min_length=1, max_length=10, description="股票代码")
    market: str = Field("A", pattern="^(A|HK|US)$", description="市场类型")
    strategy: str = Field("comprehensive", description="分析策略")
    analysis_date: Optional[str] = Field(
        None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="分析日期，格式 YYYY-MM-DD；TradingAgents 会使用该日期作为交易日",
    )


class AnalysisResponse(BaseModel):
    """分析响应"""
    symbol: str
    score: float = Field(..., ge=0, le=100)
    signal: str = Field(..., pattern="^(buy|sell|hold)$")
    trend: str = Field(..., pattern="^(bullish|bearish|neutral)$")
    reason: str


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_stock(
    request: AnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
):
    """分析股票"""
    try:
        result = await service.analyze_stock(
            request.symbol,
            request.strategy,
            context={
                "market": request.market,
                "analysis_date": request.analysis_date,
            },
        )

        return AnalysisResponse(
            symbol=request.symbol,
            score=result.score,
            signal=result.signal,
            trend=result.trend,
            reason=result.reason,
        )
    except Exception as e:
        logger.error(f"分析股票失败: {e}")
        raise AIProviderError(f"分析股票失败: {e}")


@router.get("/reports")
async def list_reports(
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """获取分析报告列表"""
    # TODO: 实现报告列表
    return []


@router.get("/strategies")
async def list_strategies():
    """获取策略列表"""
    from src.analysis.tradingagents_adapter import TRADINGAGENTS_STRATEGY_NAMES
    from src.analysis.strategies.base import STRATEGIES
    strategies = [
        {"name": name, "description": strategy.__class__.__name__}
        for name, strategy in STRATEGIES.items()
    ]
    strategies.append(
        {
            "name": "tradingagents",
            "description": "TauricResearch TradingAgents 多智能体分析",
            "aliases": sorted(TRADINGAGENTS_STRATEGY_NAMES - {"tradingagents"}),
        }
    )
    return strategies
