"""持仓管理器"""

from typing import Optional
from src.execution.gateways.base import Position, Account
from src.infra.logger import get_logger

logger = get_logger("position_manager")


class PositionManager:
    """持仓管理器"""

    def __init__(self):
        self.positions: dict[str, Position] = {}
        self.account: Optional[Account] = None

    async def sync_positions(self, positions: list[Position]):
        """同步持仓"""
        self.positions = {p.vt_symbol: p for p in positions}
        logger.info(f"同步持仓: {len(self.positions)} 个")

    async def get_position(self, vt_symbol: str) -> Optional[Position]:
        """获取持仓"""
        return self.positions.get(vt_symbol)

    async def update_position(self, trade):
        """更新持仓"""
        # TODO: 实现持仓更新
        pass

    async def calculate_pnl(self) -> float:
        """计算盈亏"""
        total_pnl = sum(p.pnl for p in self.positions.values())
        return total_pnl
