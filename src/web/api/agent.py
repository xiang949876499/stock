"""Agent API"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from pydantic import BaseModel, Field
from typing import Optional
import uuid

from src.analysis.service import AnalysisService
from src.web.deps import get_analysis_service
from src.exceptions import AIProviderError
from src.infra.logger import get_logger

logger = get_logger("agent_api")

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    """聊天请求"""
    session_id: Optional[str] = Field(None, description="会话 ID")
    message: str = Field(..., min_length=1, max_length=1000, description="消息内容")


class ChatResponse(BaseModel):
    """聊天响应"""
    session_id: str
    message: str


@router.post("/chat", response_model=ChatResponse)
async def agent_chat(
    request: ChatRequest,
    service: AnalysisService = Depends(get_analysis_service),
):
    """Agent 对话"""
    try:
        session_id = request.session_id or str(uuid.uuid4())
        response = await service.chat(session_id, request.message)

        return ChatResponse(
            session_id=session_id,
            message=response,
        )
    except Exception as e:
        logger.error(f"Agent 对话失败: {e}")
        raise AIProviderError(f"Agent 对话失败: {e}")


@router.post("/analyze")
async def agent_analyze(
    symbol: str = Query(..., min_length=1, max_length=10),
    strategy: str = Query("comprehensive"),
    service: AnalysisService = Depends(get_analysis_service),
):
    """Agent 分析"""
    try:
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
        raise AIProviderError(f"Agent 分析失败: {e}")


@router.websocket("/ws")
async def agent_websocket(
    websocket: WebSocket,
    service: AnalysisService = Depends(get_analysis_service),
):
    """Agent WebSocket"""
    await websocket.accept()
    session_id = str(uuid.uuid4())

    try:
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
