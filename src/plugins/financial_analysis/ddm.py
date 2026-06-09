"""DDM（股息贴现）估值插件

通过预测未来股息并折现来估算股票内在价值。
"""

from typing import Any, Dict, List

from src.plugins.base import AnalysisPlugin


class DDMValuationPlugin(AnalysisPlugin):
    """DDM 股息贴现估值插件"""

    @property
    def name(self) -> str:
        return "ddm_valuation"

    @property
    def description(self) -> str:
        return "DDM 股息贴现模型 - 通过预测未来股息计算股票内在价值"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "dividend_per_share": {
                "type": "float",
                "default": 0,
                "description": "每股股息（元）",
            },
            "growth_rate": {
                "type": "float",
                "default": 0.05,
                "description": "股息年增长率",
            },
            "required_return": {
                "type": "float",
                "default": 0.10,
                "description": "投资者要求回报率（折现率）",
            },
            "years": {
                "type": "int",
                "default": 10,
                "description": "预测年数",
            },
        }

    async def execute(
        self, stock_data: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行 DDM 估值

        Args:
            stock_data: 股票数据，可包含 dividend_per_share, current_price
            params: DDM 参数

        Returns:
            估值结果
        """
        dividend_per_share: float = params.get("dividend_per_share", 0)
        growth_rate: float = params.get("growth_rate", 0.05)
        required_return: float = params.get("required_return", 0.10)
        years: int = params.get("years", 10)

        # 从 stock_data 获取默认股息
        if dividend_per_share <= 0:
            dividend_per_share = float(
                stock_data.get("dividend_per_share", 0)
            )

        current_price: float = float(stock_data.get("current_price", 0))

        if dividend_per_share <= 0:
            return {
                "error": "每股股息必须大于 0",
                "intrinsic_value": 0,
                "current_price": current_price,
                "upside_pct": 0,
            }

        if required_return <= growth_rate:
            return {
                "error": "要求回报率必须大于增长率",
                "intrinsic_value": 0,
                "current_price": current_price,
                "upside_pct": 0,
            }

        # --- 多阶段 DDM ---
        # 前 N 年股息预测
        dividend_projections: List[Dict[str, Any]] = []
        total_pv_dividends = 0.0
        dps = dividend_per_share

        for year in range(1, years + 1):
            dps = dps * (1 + growth_rate)
            pv = dps / ((1 + required_return) ** year)
            total_pv_dividends += pv
            dividend_projections.append({
                "year": year,
                "dividend": round(dps, 4),
                "present_value": round(pv, 4),
            })

        # 终值（Gordon Growth Model）
        terminal_dividend = dps * (1 + growth_rate)
        terminal_value = terminal_dividend / (required_return - growth_rate)
        pv_terminal_value = terminal_value / ((1 + required_return) ** years)

        # 内在价值
        intrinsic_value = total_pv_dividends + pv_terminal_value

        # 上行空间
        upside_pct = (
            (intrinsic_value - current_price) / current_price * 100
            if current_price > 0
            else 0.0
        )

        # 股息收益率
        dividend_yield = (
            dividend_per_share / current_price * 100
            if current_price > 0
            else 0.0
        )

        return {
            "intrinsic_value": round(intrinsic_value, 2),
            "current_price": current_price,
            "upside_pct": round(upside_pct, 2),
            "dividend_per_share": round(dividend_per_share, 4),
            "growth_rate_pct": round(growth_rate * 100, 2),
            "required_return_pct": round(required_return * 100, 2),
            "dividend_yield_pct": round(dividend_yield, 2),
            "pv_dividends": round(total_pv_dividends, 2),
            "terminal_value": round(terminal_value, 2),
            "pv_terminal_value": round(pv_terminal_value, 2),
            "projection_years": years,
            "dividend_projections": dividend_projections,
        }
