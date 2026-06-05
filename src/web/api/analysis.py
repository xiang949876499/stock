"""分析 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from src.analysis.service import AnalysisService
from src.analysis.ai.factory import AIModelFactory
from src.config import get_settings
from src.infra.logger import get_logger

logger = get_logger("analysis_api")

router = APIRouter(prefix="/analysis", tags=["analysis"])

# 分析服务实例（延迟初始化）
_analysis_service: Optional[AnalysisService] = None


def get_analysis_service() -> AnalysisService:
    """获取分析服务"""
    global _analysis_service
    if _analysis_service is None:
        config = get_settings()
        ai_adapter = AIModelFactory.create(config)
        _analysis_service = AnalysisService(ai_adapter)
    return _analysis_service


class AnalysisRequest(BaseModel):
    """分析请求"""
    symbol: str
    market: str = "A"
    strategy: str = "comprehensive"


class AnalysisResponse(BaseModel):
    """分析响应"""
    symbol: str
    score: float
    signal: str
    trend: str
    reason: str


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_stock(request: AnalysisRequest):
    """分析股票"""
    try:
        service = get_analysis_service()
        result = await service.analyze_stock(request.symbol, request.strategy)

        return AnalysisResponse(
            symbol=request.symbol,
            score=result.score,
            signal=result.signal,
            trend=result.trend,
            reason=result.reason,
        )
    except Exception as e:
        logger.error(f"分析股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
    from src.analysis.strategies.base import STRATEGIES
    return [
        {"name": name, "description": strategy.__class__.__name__}
        for name, strategy in STRATEGIES.items()
    ]
