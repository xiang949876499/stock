"""执行服务"""

from typing import Optional
from src.execution.bridge.signal_bridge import SignalBridge, OrderPlan
from src.execution.risk.risk_manager import RiskManager, RiskConfig
from src.execution.position.manager import PositionManager
from src.execution.cn_rules import CNRules
from src.execution.security import KillSwitch
from src.research.signals.generator import Signal
from src.infra.logger import get_logger

logger = get_logger("execution_service")


class ExecutionService:
    """执行服务"""

    def __init__(
        self,
        risk_config: Optional[RiskConfig] = None,
    ):
        self.risk_manager = RiskManager(risk_config)
        self.cn_rules = CNRules()
        self.signal_bridge = SignalBridge(
            self.risk_manager,
            cn_rules=self.cn_rules,
        )
        self.position_manager = PositionManager()

    async def process_signal(
        self,
        signal: Signal,
        current_positions: Optional[dict[str, float]] = None
    ) -> list[OrderPlan]:
        """处理信号"""
        # 检查 kill switch
        if KillSwitch.check():
            logger.warning("交易已禁用")
            return []

        return await self.signal_bridge.process_signal(signal, current_positions)

    async def get_positions(self):
        """获取持仓"""
        return self.position_manager.positions

    async def get_account(self):
        """获取账户"""
        return self.position_manager.account

    async def calculate_pnl(self):
        """计算盈亏"""
        return await self.position_manager.calculate_pnl()

    def generate_execution_plan(
        self,
        orders: list[OrderPlan],
        total_equity: float,
        prices: dict[str, float],
    ) -> list[dict]:
        """生成执行计划"""
        return self.signal_bridge.generate_execution_plan(orders, total_equity, prices)
