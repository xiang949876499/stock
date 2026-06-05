"""信号契约 v1"""

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel


class SignalStatus(str, Enum):
    """信号状态"""
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"
    CONSUMED = "consumed"
    ARCHIVED = "archived"


class SignalSource(str, Enum):
    """信号来源"""
    QLIB = "qlib"
    VNPY_ALPHA = "vnpy_alpha"
    MANUAL = "manual"
    LLM_PROPOSED = "llm_proposed"
    FINRL_X = "finrl_x"


class SignalV1(BaseModel):
    """信号契约 v1"""
    schema_version: str = "v1"
    signal_id: str
    as_of: datetime
    valid_until: Optional[datetime] = None
    universe: Optional[str] = None
    source: SignalSource
    status: SignalStatus
    targets: dict[str, float]
    cash_weight: float = 0.0
    risk_overlay: Optional[dict] = None
    metadata: Optional[dict] = None
