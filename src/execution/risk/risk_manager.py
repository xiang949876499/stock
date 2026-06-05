"""风控管理器"""

from dataclasses import dataclass
from typing import Optional

from src.research.signals.generator import Signal
from src.infra.logger import get_logger

logger = get_logger("risk_manager")


@dataclass
class RiskConfig:
    """风控配置"""
    max_position_ratio: float = 0.3
    max_daily_loss: float = 0.05
    max_drawdown: float = 0.1
    max_single_position: float = 0.1
    max_order_value: float = 100000.0


@dataclass
class RiskCheckResult:
    """风控检查结果"""
    passed: bool
    reason: str = ""


class RiskManager:
    """风控管理器"""

    def __init__(self, config: Optional[RiskConfig] = None):
        """初始化风控管理器"""
        self.config = config or RiskConfig()
        self.daily_pnl = 0.0
        self.max_drawdown = 0.0

    async def check_signal(self, signal: Signal) -> RiskCheckResult:
        """检查信号是否通过风控"""
        # 检查总权重
        total_weight = sum(signal.targets.values()) + signal.cash_weight
        if total_weight > 1.01:
            return RiskCheckResult(
                passed=False,
                reason=f"总权重 {total_weight} 超过 1"
            )

        # 检查单标的上限
        max_single = self.config.max_single_position
        if signal.risk_overlay:
            max_single = signal.risk_overlay.get("max_single_name_weight", max_single)

        for symbol, weight in signal.targets.items():
            if weight > max_single:
                return RiskCheckResult(
                    passed=False,
                    reason=f"{symbol} 权重 {weight} 超过上限 {max_single}"
                )

        # 检查日亏损
        if self.daily_pnl < -self.config.max_daily_loss:
            return RiskCheckResult(
                passed=False,
                reason=f"今日亏损 {self.daily_pnl} 超过限制 {self.config.max_daily_loss}"
            )

        # 检查最大回撤
        if self.max_drawdown > self.config.max_drawdown:
            return RiskCheckResult(
                passed=False,
                reason=f"最大回撤 {self.max_drawdown} 超过限制 {self.config.max_drawdown}"
            )

        return RiskCheckResult(passed=True)

    def update_pnl(self, pnl: float):
        """更新盈亏"""
        self.daily_pnl += pnl

    def reset_daily(self):
        """重置每日统计"""
        self.daily_pnl = 0.0
