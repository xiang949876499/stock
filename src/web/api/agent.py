"""Agent API"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

from src.analysis.service import AnalysisService
from src.analysis.ai.factory import AIModelFactory
from src.config import get_settings
from src.infra.logger import get_logger

logger = get_logger("agent_api")

router = APIRouter(prefix="/agent", tags=["agent"])

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


class ChatRequest(BaseModel):
    """聊天请求"""
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str
    message: str


@router.post("/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """Agent 对话"""
    try:
        service = get_analysis_service()
        session_id = request.session_id or str(uuid.uuid4())

        response = await service.chat(session_id, request.message)

        return ChatResponse(
            session_id=session_id,
            message=response,
        )
    except Exception as e:
        logger.error(f"Agent 对话失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def agent_analyze(
    symbol: str,
    strategy: str = "comprehensive",
):
    """Agent 分析"""
    try:
        service = get_analysis_service()
        result = await service.analyze_stock(symbol, strategy)

        return {
            "symbol": symbol,
            "score": result.score,
            "signal": result.signal,
            "trend": result.trend,
            "reason": result.reason,
        }
    except Exception as e:
        logger.error(f"Agent 分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws")
async def agent_websocket(websocket: WebSocket):
    """Agent WebSocket"""
    await websocket.accept()
    session_id = str(uuid.uuid4())

    try:
        service = get_analysis_service()

        while True:
            # 接收消息
            data = await websocket.receive_json()
            message = data.get("message", "")

            if not message:
                continue

            # 获取回复
            response = await service.chat(session_id, message)

            # 发送回复
            await websocket.send_json({
                'type': 'message',
                'content': response,
                'session_id': session_id,
            })

    except WebSocketDisconnect:
        # 清理会话
        service.clear_session(session_id)
        logger.info(f"WebSocket 断开: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
        await websocket.close()
