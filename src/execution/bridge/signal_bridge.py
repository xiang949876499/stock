"""信号桥接器"""

from datetime import date
from typing import Optional
from dataclasses import dataclass

from src.research.signals.generator import Signal, SignalStatus
from src.execution.risk.risk_manager import RiskManager, RiskCheckResult
from src.execution.cn_rules import CNRules
from src.data.catalog.manager import InstrumentCatalog
from src.infra.logger import get_logger

logger = get_logger("signal_bridge")


@dataclass
class OrderPlan:
    """订单计划"""
    vt_symbol: str
    side: str  # BUY / SELL / HOLD
    target_weight: float
    current_weight: float
    volume: int = 0
    price: float = 0.0
    order_type: str = "LIMIT"


class SignalBridge:
    """信号桥接器：将 signals/v1 转换为订单"""

    def __init__(
        self,
        risk_manager: Optional[RiskManager] = None,
        catalog: Optional[InstrumentCatalog] = None,
        cn_rules: Optional[CNRules] = None,
    ):
        """初始化信号桥接器"""
        self.risk_manager = risk_manager or RiskManager()
        self.catalog = catalog or InstrumentCatalog()
        self.cn_rules = cn_rules or CNRules()

    async def process_signal(
        self,
        signal: Signal,
        current_positions: Optional[dict[str, float]] = None
    ) -> list[OrderPlan]:
        """处理信号，生成订单计划"""
        # 检查信号状态
        if signal.status != SignalStatus.PUBLISHED:
            logger.warning(f"信号状态不是 published: {signal.status}")
            return []

        # 风控检查
        risk_check = await self.risk_manager.check_signal(signal)
        if not risk_check.passed:
            logger.warning(f"信号被风控拒绝: {risk_check.reason}")
            return []

        # 获取当前持仓
        if current_positions is None:
            current_positions = {}

        # 生成订单计划
        orders = []
        for vt_symbol, target_weight in signal.targets.items():
            current_weight = current_positions.get(vt_symbol, 0.0)
            weight_diff = target_weight - current_weight

            # 判断方向
            if weight_diff > 0.01:
                side = "BUY"
            elif weight_diff < -0.01:
                side = "SELL"
            else:
                side = "HOLD"

            if side != "HOLD":
                order = OrderPlan(
                    vt_symbol=vt_symbol,
                    side=side,
                    target_weight=target_weight,
                    current_weight=current_weight,
                )
                orders.append(order)
                logger.info(f"生成订单计划: {vt_symbol} {side} {weight_diff:.2%}")

        return orders

    def calculate_volume(
        self,
        order: OrderPlan,
        total_equity: float,
        last_price: float,
        lot_size: int = 100
    ) -> int:
        """计算订单数量"""
        # 计算目标金额
        weight_diff = abs(order.target_weight - order.current_weight)
        target_value = total_equity * weight_diff

        # 使用 CNRules 计算数量
        volume = self.cn_rules.weight_to_volume(
            weight=weight_diff,
            total_equity=total_equity,
            last_price=last_price,
            lot_size=lot_size,
        )

        return volume

    def validate_order(
        self,
        order: OrderPlan,
        last_price: float,
        last_close: float,
    ) -> tuple[bool, str]:
        """验证订单"""
        # 检查涨跌停
        if not self.cn_rules.check_price_limit(order.vt_symbol, last_price, last_close):
            return False, "触及涨跌停"

        # 检查数量
        if order.volume <= 0:
            return False, "数量无效"

        return True, ""

    def generate_execution_plan(
        self,
        orders: list[OrderPlan],
        total_equity: float,
        prices: dict[str, float],
    ) -> list[dict]:
        """生成执行计划"""
        execution_plan = []

        for order in orders:
            last_price = prices.get(order.vt_symbol, 0)
            if last_price == 0:
                logger.warning(f"无法获取价格: {order.vt_symbol}")
                continue

            # 计算数量
            volume = self.calculate_volume(order, total_equity, last_price)
            if volume == 0:
                continue

            execution_plan.append({
                "vt_symbol": order.vt_symbol,
                "side": order.side,
                "volume": volume,
                "price": last_price,
                "order_type": order.order_type,
            })

        return execution_plan
