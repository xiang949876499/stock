"""WebSocket 管理器"""

from typing import Optional
from fastapi import WebSocket

from src.infra.logger import get_logger

logger = get_logger("websocket")


class WebSocketManager:
    """WebSocket 管理器"""

    def __init__(self):
        self.connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """连接"""
        await websocket.accept()
        self.connections[client_id] = websocket
        logger.info(f"WebSocket 连接: {client_id}")

    async def disconnect(self, client_id: str):
        """断开"""
        if client_id in self.connections:
            del self.connections[client_id]
            logger.info(f"WebSocket 断开: {client_id}")

    async def broadcast(self, message: dict):
        """广播"""
        for client_id, websocket in self.connections.items():
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"广播失败: {client_id}, {e}")
                await self.disconnect(client_id)

    async def send_personal(self, client_id: str, message: dict):
        """发送个人消息"""
        websocket = self.connections.get(client_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"发送失败: {client_id}, {e}")
                await self.disconnect(client_id)
