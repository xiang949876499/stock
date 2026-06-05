"""国内交易规则"""

from datetime import date
from typing import Optional
from src.infra.logger import get_logger

logger = get_logger("cn_rules")


class CNRules:
    """国内交易规则"""

    # A 股现货规则
    A_STOCK_RULES = {
        "lot_size": 100,
        "t_plus_1": True,
        "price_limit": 0.10,       # 涨跌停 10%
        "price_limit_st": 0.05,    # ST 涨跌停 5%
        "price_limit_kcb": 0.20,   # 科创板涨跌停 20%
    }

    # 港股规则
    HK_RULES = {
        "lot_size": 100,
        "t_plus_0": True,
        "price_limit": None,
    }

    def check_t_plus_1(
        self,
        vt_symbol: str,
        side: str,
        positions: list
    ) -> bool:
        """检查 T+1 规则"""
        if side == "SELL":
            today = date.today()
            for pos in positions:
                if pos.vt_symbol == vt_symbol and pos.open_date == today:
                    return False
        return True

    def check_price_limit(
        self,
        vt_symbol: str,
        price: float,
        last_close: float
    ) -> bool:
        """检查涨跌停"""
        if last_close == 0:
            return True

        pct_change = (price - last_close) / last_close
        limit = self._get_price_limit(vt_symbol)
        return abs(pct_change) <= limit

    def round_to_lot(
        self,
        volume: float,
        lot_size: int
    ) -> int:
        """取整到最小交易单位"""
        return int(volume // lot_size) * lot_size

    def weight_to_volume(
        self,
        weight: float,
        total_equity: float,
        last_price: float,
        lot_size: int,
        contract_size: int = 1
    ) -> int:
        """权重转股数/手数"""
        if last_price == 0:
            return 0

        target_value = total_equity * weight
        volume = target_value / last_price / contract_size
        return self.round_to_lot(volume, lot_size)

    def _get_price_limit(self, vt_symbol: str) -> float:
        """获取涨跌停限制"""
        # 科创板
        if vt_symbol.startswith("688"):
            return self.A_STOCK_RULES["price_limit_kcb"]
        # ST 股票
        # TODO: 从 catalog 获取是否 ST
        return self.A_STOCK_RULES["price_limit"]
