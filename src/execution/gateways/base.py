"""网关基类"""

from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass


@dataclass
class Order:
    """订单"""
    vt_symbol: str
    direction: str  # LONG / SHORT
    offset: str  # OPEN / CLOSE
    price: float
    volume: int
    order_type: str = "LIMIT"  # LIMIT / MARKET


@dataclass
class Trade:
    """成交"""
    vt_symbol: str
    direction: str
    offset: str
    price: float
    volume: int
    trade_id: str


@dataclass
class Position:
    """持仓"""
    vt_symbol: str
    direction: str
    volume: int
    price: float
    pnl: float


@dataclass
class Account:
    """账户"""
    account_id: str
    balance: float
    available: float
    frozen: float


class BaseGateway(ABC):
    """网关基类"""

    def __init__(self, gateway_name: str):
        self.gateway_name = gateway_name

    @abstractmethod
    async def connect(self, config: dict):
        """连接"""
        pass

    @abstractmethod
    async def disconnect(self):
        """断开"""
        pass

    @abstractmethod
    async def send_order(self, order: Order) -> str:
        """发送委托"""
        pass

    @abstractmethod
    async def cancel_order(self, vt_orderid: str):
        """撤销委托"""
        pass

    @abstractmethod
    async def get_positions(self) -> list[Position]:
        """获取持仓"""
        pass

    @abstractmethod
    async def get_account(self) -> Account:
        """获取账户"""
        pass
