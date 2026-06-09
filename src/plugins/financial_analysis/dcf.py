"""DCF（现金流折现）估值插件

通过预测未来自由现金流并折现来估算企业内在价值。
"""

from typing import Any, Dict, List

from src.plugins.base import AnalysisPlugin


class DCFValuationPlugin(AnalysisPlugin):
    """DCF 现金流折现估值插件"""

    @property
    def name(self) -> str:
        return "dcf_valuation"

    @property
    def description(self) -> str:
        return "DCF 现金流折现估值模型 - 通过预测未来现金流计算企业内在价值"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "years": {
                "type": "int",
                "default": 5,
                "description": "预测年数",
            },
            "growth_rate": {
                "type": "float",
                "default": 0.15,
                "description": "前N年自由现金流年增长率",
            },
            "terminal_growth": {
                "type": "float",
                "default": 0.03,
                "description": "永续增长率（终值增长率）",
            },
            "wacc": {
                "type": "float",
                "default": 0.10,
                "description": "加权平均资本成本（折现率）",
            },
        }

    async def execute(
        self, stock_data: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行 DCF 估值

        Args:
            stock_data: 股票数据，需包含 net_profit, total_shares, current_price
            params: DCF 参数

        Returns:
            估值结果
        """
        years: int = params.get("years", 5)
        growth_rate: float = params.get("growth_rate", 0.15)
        terminal_growth: float = params.get("terminal_growth", 0.03)
        wacc: float = params.get("wacc", 0.10)

        # 以净利润作为自由现金流的近似值
        base_cf: float = float(stock_data.get("net_profit", 0))
        current_price: float = float(stock_data.get("current_price", 0))
        total_shares: float = float(stock_data.get("total_shares", 1))

        # --- 预测未来现金流 ---
        cash_flows: List[float] = []
        cf = base_cf
        for _ in range(years):
            cf = cf * (1 + growth_rate)
            cash_flows.append(cf)

        # --- 计算终值 (Gordon Growth Model) ---
        terminal_cf = cash_flows[-1] * (1 + terminal_growth)
        terminal_value = terminal_cf / (wacc - terminal_growth)

        # --- 折现计算 ---
        pv_cash_flows = 0.0
        for i, annual_cf in enumerate(cash_flows, start=1):
            pv_cash_flows += annual_cf / ((1 + wacc) ** i)

        pv_terminal_value = terminal_value / ((1 + wacc) ** years)

        enterprise_value = pv_cash_flows + pv_terminal_value

        # 简化处理：股权价值 = 企业价值（未扣净债务）
        equity_value = enterprise_value
        per_share_value = equity_value / total_shares if total_shares > 0 else 0.0

        upside_pct = (
            ((per_share_value - current_price) / current_price * 100)
            if current_price > 0
            else 0.0
        )

        return {
            "enterprise_value": round(enterprise_value, 2),
            "equity_value": round(equity_value, 2),
            "per_share_value": round(per_share_value, 2),
            "current_price": current_price,
            "upside_pct": round(upside_pct, 2),
            "cash_flows": [round(cf, 2) for cf in cash_flows],
            "terminal_value": round(terminal_value, 2),
            "pv_cash_flows": round(pv_cash_flows, 2),
            "pv_terminal_value": round(pv_terminal_value, 2),
        }
