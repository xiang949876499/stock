"""会话管理"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Message(BaseModel):
    """消息"""
    role: str  # user/assistant/system
    content: str
    timestamp: datetime = None

    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now()
        super().__init__(**data)


class ChatSession:
    """聊天会话"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.messages: list[Message] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_message(self, role: str, content: str):
        """添加消息"""
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()

    def get_messages(self) -> list[dict]:
        """获取消息列表"""
        return [
            {"role": m.role, "content": m.content}
            for m in self.messages
        ]

    def clear(self):
        """清空会话"""
        self.messages.clear()
        self.updated_at = datetime.now()
