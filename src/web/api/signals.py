"""信号 API"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from pydantic import BaseModel, Field

from src.research.service import ResearchService
from src.web.deps import get_research_service
from src.exceptions import SignalError, ValidationError
from src.infra.logger import get_logger

logger = get_logger("signals_api")

router = APIRouter(prefix="/signals", tags=["signals"])


class CreateSignalRequest(BaseModel):
    """创建信号请求"""
    targets: dict[str, float] = Field(..., description="目标权重")
    source: str = Field("manual", pattern="^(qlib|vnpy_alpha|manual|llm_proposed|finrl_x)$")
    universe: Optional[str] = Field(None, description="股票池")
    cash_weight: float = Field(0.0, ge=0, le=1, description="现金权重")


@router.get("/")
async def list_signals(
    symbol: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """获取信号列表"""
    # TODO: 从数据库获取信号
    return []


@router.post("/")
async def create_signal(
    request: CreateSignalRequest,
    service: ResearchService = Depends(get_research_service),
):
    """创建信号"""
    try:
        signal = service.create_signal(
            targets=request.targets,
            source=request.source,
            universe=request.universe,
            cash_weight=request.cash_weight,
        )

        # 验证信号
        is_valid, issues = service.validate_signal(signal)
        if not is_valid:
            raise ValidationError(f"信号验证失败: {', '.join(issues)}")

        return signal
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"创建信号失败: {e}")
        raise SignalError(f"创建信号失败: {e}")


@router.post("/{signal_id}/approve")
async def approve_signal(
    signal_id: str,
    service: ResearchService = Depends(get_research_service),
):
    """审批信号"""
    try:
        # TODO: 从数据库获取信号并审批
        return {"signal_id": signal_id, "status": "approved"}
    except Exception as e:
        logger.error(f"审批信号失败: {e}")
        raise SignalError(f"审批信号失败: {e}")


@router.post("/{signal_id}/reject")
async def reject_signal(
    signal_id: str,
    reason: str = Query("", description="拒绝原因"),
    service: ResearchService = Depends(get_research_service),
):
    """拒绝信号"""
    try:
        # TODO: 从数据库获取信号并拒绝
        return {"signal_id": signal_id, "status": "rejected", "reason": reason}
    except Exception as e:
        logger.error(f"拒绝信号失败: {e}")
        raise SignalError(f"拒绝信号失败: {e}")


@router.post("/{signal_id}/publish")
async def publish_signal(
    signal_id: str,
    service: ResearchService = Depends(get_research_service),
):
    """发布信号"""
    try:
        # TODO: 从数据库获取信号并发布
        return {"signal_id": signal_id, "status": "published"}
    except Exception as e:
        logger.error(f"发布信号失败: {e}")
        raise SignalError(f"发布信号失败: {e}")
