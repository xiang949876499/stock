"""信号 API"""

from fastapi import APIRouter, HTTPException
from typing import Optional
from pydantic import BaseModel

from src.research.service import ResearchService
from src.infra.logger import get_logger

logger = get_logger("signals_api")

router = APIRouter(prefix="/signals", tags=["signals"])

# 研究服务实例（延迟初始化）
_research_service: Optional[ResearchService] = None


def get_research_service() -> ResearchService:
    """获取研究服务"""
    global _research_service
    if _research_service is None:
        _research_service = ResearchService()
    return _research_service


class CreateSignalRequest(BaseModel):
    """创建信号请求"""
    targets: dict[str, float]
    source: str = "manual"
    universe: Optional[str] = None
    cash_weight: float = 0.0


@router.get("/")
async def list_signals(
    symbol: Optional[str] = None,
    status: Optional[str] = None,
):
    """获取信号列表"""
    # TODO: 从数据库获取信号
    return []


@router.post("/")
async def create_signal(request: CreateSignalRequest):
    """创建信号"""
    try:
        service = get_research_service()
        signal = service.create_signal(
            targets=request.targets,
            source=request.source,
            universe=request.universe,
            cash_weight=request.cash_weight,
        )

        # 验证信号
        is_valid, issues = service.validate_signal(signal)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"信号验证失败: {issues}")

        return signal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建信号失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{signal_id}/approve")
async def approve_signal(signal_id: str):
    """审批信号"""
    try:
        # TODO: 从数据库获取信号并审批
        return {"signal_id": signal_id, "status": "approved"}
    except Exception as e:
        logger.error(f"审批信号失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{signal_id}/reject")
async def reject_signal(signal_id: str, reason: str = ""):
    """拒绝信号"""
    try:
        # TODO: 从数据库获取信号并拒绝
        return {"signal_id": signal_id, "status": "rejected", "reason": reason}
    except Exception as e:
        logger.error(f"拒绝信号失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{signal_id}/publish")
async def publish_signal(signal_id: str):
    """发布信号"""
    try:
        # TODO: 从数据库获取信号并发布
        return {"signal_id": signal_id, "status": "published"}
    except Exception as e:
        logger.error(f"发布信号失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
