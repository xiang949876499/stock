"""Easytrader 实盘交易适配器"""

from typing import Optional
from dataclasses import dataclass

from src.integrations.base import BaseAdapter
from src.integrations.easytrader.brokers import BrokerType, BROKER_CONFIGS
from src.infra.logger import get_logger

logger = get_logger("easytrader_adapter")


@dataclass
class TradeResult:
    """交易结果"""
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    data: Optional[dict] = None


class EasytraderAdapter(BaseAdapter):
    """Easytrader 实盘交易适配器"""

    def __init__(self, broker: str = "ths", enabled: bool = True):
        super().__init__(name="easytrader", enabled=enabled)
        self.broker = broker
        self.trader = None
        self.connected = False

    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            import easytrader
            self.logger.info("Easytrader 初始化成功")
            return True
        except ImportError as e:
            self.logger.error(f"Easytrader 未安装: {e}")
            return False

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            import easytrader
            return self.connected
        except ImportError:
            return False

    def list_brokers(self) -> list[str]:
        """列出支持的券商"""
        return [b.value for b in BrokerType]

    async def connect(self, account_path: Optional[str] = None) -> TradeResult:
        """
        连接券商客户端

        Args:
            account_path: 账户配置文件路径
        """
        try:
            import easytrader

            self.trader = easytrader.use(self.broker)

            if account_path:
                self.trader.prepare(account_path)

            self.connected = True
            self.logger.info(f"连接券商成功: {self.broker}")

            return TradeResult(success=True, message="连接成功")
        except Exception as e:
            self.logger.error(f"连接券商失败: {e}")
            return TradeResult(success=False, message=str(e))

    async def disconnect(self) -> TradeResult:
        """断开连接"""
        self.trader = None
        self.connected = False
        return TradeResult(success=True, message="已断开")

    async def buy(
        self,
        symbol: str,
        price: float,
        amount: int,
    ) -> TradeResult:
        """
        买入

        Args:
            symbol: 股票代码
            price: 价格
            amount: 数量
        """
        if not self.connected:
            return TradeResult(success=False, message="未连接券商")

        try:
            result = self.trader.buy(symbol, price=price, amount=amount)
            self.logger.info(f"买入成功: {symbol} {amount}股 @ {price}")

            return TradeResult(
                success=True,
                order_id=result.get('entrust_no'),
                message="买入成功",
                data=result,
            )
        except Exception as e:
            self.logger.error(f"买入失败: {e}")
            return TradeResult(success=False, message=str(e))

    async def sell(
        self,
        symbol: str,
        price: float,
        amount: int,
    ) -> TradeResult:
        """
        卖出

        Args:
            symbol: 股票代码
            price: 价格
            amount: 数量
        """
        if not self.connected:
            return TradeResult(success=False, message="未连接券商")

        try:
            result = self.trader.sell(symbol, price=price, amount=amount)
            self.logger.info(f"卖出成功: {symbol} {amount}股 @ {price}")

            return TradeResult(
                success=True,
                order_id=result.get('entrust_no'),
                message="卖出成功",
                data=result,
            )
        except Exception as e:
            self.logger.error(f"卖出失败: {e}")
            return TradeResult(success=False, message=str(e))

    async def get_balance(self) -> dict:
        """查询资金"""
        if not self.connected:
            return {}

        try:
            return self.trader.balance
        except Exception as e:
            self.logger.error(f"查询资金失败: {e}")
            return {}

    async def get_positions(self) -> list[dict]:
        """查询持仓"""
        if not self.connected:
            return []

        try:
            return self.trader.position
        except Exception as e:
            self.logger.error(f"查询持仓失败: {e}")
            return []

    async def cancel_order(self, order_id: str) -> TradeResult:
        """撤单"""
        if not self.connected:
            return TradeResult(success=False, message="未连接券商")

        try:
            self.trader.cancel_entrust(order_id)
            self.logger.info(f"撤单成功: {order_id}")
            return TradeResult(success=True, message="撤单成功")
        except Exception as e:
            self.logger.error(f"撤单失败: {e}")
            return TradeResult(success=False, message=str(e))
