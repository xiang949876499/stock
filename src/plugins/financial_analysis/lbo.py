"""LBO（杠杆收购）分析插件

通过杠杆收购模型计算投资回报率、MOIC、债务偿还等关键指标。
"""

from typing import Any, Dict, List

from src.plugins.base import AnalysisPlugin


class LBOAnalysisPlugin(AnalysisPlugin):
    """LBO 杠杆收购分析插件"""

    @property
    def name(self) -> str:
        return "lbo_analysis"

    @property
    def description(self) -> str:
        return "LBO 杠杆收购模型 - 计算杠杆收购投资回报、MOIC、债务偿还等指标"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "purchase_price": {
                "type": "float",
                "default": 0,
                "description": "收购价格（元）",
            },
            "debt_ratio": {
                "type": "float",
                "default": 0.60,
                "description": "债务占比（0-1），如 0.60 表示 60% 债务融资",
            },
            "interest_rate": {
                "type": "float",
                "default": 0.05,
                "description": "债务年利率",
            },
            "exit_multiple": {
                "type": "float",
                "default": 10.0,
                "description": "退出时 EV/EBITDA 倍数",
            },
            "holding_period": {
                "type": "int",
                "default": 5,
                "description": "持有期（年）",
            },
        }

    async def execute(
        self, stock_data: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行 LBO 分析

        Args:
            stock_data: 股票数据，需包含 current_price, ebitda, total_shares
            params: LBO 参数

        Returns:
            杠杆收购分析结果
        """
        purchase_price: float = params.get("purchase_price", 0)
        debt_ratio: float = params.get("debt_ratio", 0.60)
        interest_rate: float = params.get("interest_rate", 0.05)
        exit_multiple: float = params.get("exit_multiple", 10.0)
        holding_period: int = params.get("holding_period", 5)

        # 从 stock_data 获取数据
        current_price: float = float(stock_data.get("current_price", 0))
        ebitda: float = float(stock_data.get("ebitda", 0))
        total_shares: float = float(stock_data.get("total_shares", 1))
        ebitda_growth: float = float(
            params.get("ebitda_growth", 0.08)
        )

        # 如果未指定收购价格，使用当前市值
        if purchase_price <= 0:
            purchase_price = current_price * total_shares

        # --- 资本结构 ---
        debt_amount = purchase_price * debt_ratio
        equity_amount = purchase_price * (1 - debt_ratio)

        # --- 持有期间 EBITDA 增长与债务偿还 ---
        yearly_data: List[Dict[str, Any]] = []
        remaining_debt = debt_amount
        current_ebitda = ebitda

        for year in range(1, holding_period + 1):
            # EBITDA 增长
            current_ebitda = current_ebitda * (1 + ebitda_growth)

            # 年度自由现金流用于偿还债务（简化：EBITDA * 50% 作为可偿债现金流）
            fcf_for_debt = current_ebitda * 0.50

            # 利息支出
            interest_expense = remaining_debt * interest_rate

            # 本金偿还（自由现金流 - 利息）
            principal_payment = max(0, fcf_for_debt - interest_expense)
            principal_payment = min(principal_payment, remaining_debt)
            remaining_debt = max(0, remaining_debt - principal_payment)

            yearly_data.append({
                "year": year,
                "ebitda": round(current_ebitda, 2),
                "fcf_for_debt": round(fcf_for_debt, 2),
                "interest_expense": round(interest_expense, 2),
                "principal_payment": round(principal_payment, 2),
                "remaining_debt": round(remaining_debt, 2),
            })

        # --- 退出估值 ---
        exit_ebitda = current_ebitda
        exit_enterprise_value = exit_ebitda * exit_multiple
        exit_equity_value = exit_enterprise_value - remaining_debt

        # --- 投资回报计算 ---
        moic = exit_equity_value / equity_amount if equity_amount > 0 else 0
        # IRR 近似计算：(MOIC ^ (1/n)) - 1
        if moic > 0 and holding_period > 0:
            irr = moic ** (1 / holding_period) - 1
        else:
            irr = 0.0

        debt_paydown = debt_amount - remaining_debt
        debt_paydown_pct = (
            debt_paydown / debt_amount * 100 if debt_amount > 0 else 0
        )

        return {
            "purchase_price": round(purchase_price, 2),
            "equity_invested": round(equity_amount, 2),
            "debt_at_entry": round(debt_amount, 2),
            "debt_ratio_pct": round(debt_ratio * 100, 2),
            "interest_rate_pct": round(interest_rate * 100, 2),
            "holding_period": holding_period,
            "exit_ebitda": round(exit_ebitda, 2),
            "exit_multiple": exit_multiple,
            "exit_enterprise_value": round(exit_enterprise_value, 2),
            "exit_equity_value": round(exit_equity_value, 2),
            "moic": round(moic, 2),
            "equity_irr_pct": round(irr * 100, 2),
            "debt_paydown": round(debt_paydown, 2),
            "debt_paydown_pct": round(debt_paydown_pct, 2),
            "remaining_debt": round(remaining_debt, 2),
            "yearly_projections": yearly_data,
        }
