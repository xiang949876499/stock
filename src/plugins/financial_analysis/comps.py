"""可比公司分析插件

通过同行业公司的估值指标对比，评估目标公司相对估值水平。
"""

from typing import Any, Dict, List

from src.plugins.base import AnalysisPlugin


# 模拟同行数据（实际生产中应从数据源获取）
MOCK_PEER_DATA: Dict[str, Dict[str, float]] = {
    "000858": {
        "name": "五粮液",
        "pe_ratio": 22.5,
        "pb_ratio": 6.8,
        "ps_ratio": 8.3,
        "ev_ebitda": 16.2,
        "current_price": 150.0,
        "eps": 6.67,
        "bvps": 22.06,
        "revenue_per_share": 18.07,
        "ebitda_per_share": 9.26,
    },
    "002304": {
        "name": "洋河股份",
        "pe_ratio": 18.3,
        "pb_ratio": 4.5,
        "ps_ratio": 5.6,
        "ev_ebitda": 13.1,
        "current_price": 120.0,
        "eps": 6.56,
        "bvps": 26.67,
        "revenue_per_share": 21.43,
        "ebitda_per_share": 9.16,
    },
    "000568": {
        "name": "泸州老窖",
        "pe_ratio": 25.1,
        "pb_ratio": 8.2,
        "ps_ratio": 11.5,
        "ev_ebitda": 19.8,
        "current_price": 200.0,
        "eps": 7.97,
        "bvps": 24.39,
        "revenue_per_share": 17.39,
        "ebitda_per_share": 10.10,
    },
    "600809": {
        "name": "山西汾酒",
        "pe_ratio": 35.2,
        "pb_ratio": 12.5,
        "ps_ratio": 14.2,
        "ev_ebitda": 26.5,
        "current_price": 250.0,
        "eps": 7.10,
        "bvps": 20.0,
        "revenue_per_share": 17.61,
        "ebitda_per_share": 9.43,
    },
    "000596": {
        "name": "古井贡酒",
        "pe_ratio": 28.6,
        "pb_ratio": 7.3,
        "ps_ratio": 9.8,
        "ev_ebitda": 20.4,
        "current_price": 180.0,
        "eps": 6.29,
        "bvps": 24.66,
        "revenue_per_share": 18.37,
        "ebitda_per_share": 8.82,
    },
}

METRIC_KEY_MAP: Dict[str, str] = {
    "PE": "pe_ratio",
    "PB": "pb_ratio",
    "PS": "ps_ratio",
    "EV/EBITDA": "ev_ebitda",
}

EPS_KEY_MAP: Dict[str, str] = {
    "PE": "eps",
    "PB": "bvps",
    "PS": "revenue_per_share",
    "EV/EBITDA": "ebitda_per_share",
}


class ComparableAnalysisPlugin(AnalysisPlugin):
    """可比公司分析插件"""

    @property
    def name(self) -> str:
        return "comparable_analysis"

    @property
    def description(self) -> str:
        return "可比公司估值分析 - 通过同行业公司对比评估目标公司相对估值水平"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "peer_codes": {
                "type": "List[str]",
                "default": [],
                "description": "同行公司股票代码列表",
            },
            "metrics": {
                "type": "List[str]",
                "default": ["PE", "PB", "PS", "EV/EBITDA"],
                "description": "用于比较的估值指标列表",
            },
        }

    async def execute(
        self, stock_data: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行可比公司分析

        Args:
            stock_data: 目标股票数据，需包含 pe_ratio, pb_ratio, ps_ratio,
                        ev_ebitda, current_price
            params: 包含 peer_codes 和 metrics

        Returns:
            可比公司分析结果
        """
        peer_codes: List[str] = params.get("peer_codes", [])
        metrics: List[str] = params.get("metrics", ["PE", "PB", "PS", "EV/EBITDA"])

        current_price: float = float(stock_data.get("current_price", 0))

        # --- 收集同行数据 ---
        peer_comparison: List[Dict[str, Any]] = []
        for code in peer_codes:
            peer = MOCK_PEER_DATA.get(code)
            if peer is None:
                continue

            entry: Dict[str, Any] = {
                "code": code,
                "name": peer["name"],
                "current_price": peer["current_price"],
                "metrics": {},
            }
            for metric in metrics:
                key = METRIC_KEY_MAP.get(metric)
                if key and key in peer:
                    entry["metrics"][metric] = round(peer[key], 2)
            peer_comparison.append(entry)

        # --- 计算同行平均估值指标 ---
        avg_metrics: Dict[str, float] = {}
        for metric in metrics:
            key = METRIC_KEY_MAP.get(metric)
            if key is None:
                continue
            values = [
                MOCK_PEER_DATA[c][key]
                for c in peer_codes
                if c in MOCK_PEER_DATA and key in MOCK_PEER_DATA[c]
            ]
            if values:
                avg_metrics[metric] = round(sum(values) / len(values), 2)

        # --- 目标公司估值 ---
        target_valuation: Dict[str, float] = {}
        for metric in metrics:
            key = METRIC_KEY_MAP.get(metric)
            if key and key in stock_data:
                target_valuation[metric] = round(float(stock_data[key]), 2)

        # --- 计算隐含价值 ---
        implied_values: Dict[str, float] = {}
        for metric in metrics:
            if metric not in avg_metrics:
                continue
            eps_key = EPS_KEY_MAP.get(metric)
            if eps_key is None:
                continue

            # 用同行平均估值指标 * 目标公司每股收益推算隐含股价
            target_metric = target_valuation.get(metric, 0)
            if target_metric > 0:
                implied_per_unit = current_price / target_metric
            else:
                implied_per_unit = 0

            implied_values[metric] = round(avg_metrics[metric] * implied_per_unit, 2)

        # 综合隐含价值（各指标隐含价值的平均）
        if implied_values:
            avg_implied = sum(implied_values.values()) / len(implied_values)
        else:
            avg_implied = current_price

        # --- 计算溢价/折价 ---
        premium_discount: Dict[str, float] = {}
        for metric, implied in implied_values.items():
            if implied > 0:
                premium_discount[metric] = round(
                    (current_price - implied) / implied * 100, 2
                )

        overall_premium = (
            round((current_price - avg_implied) / avg_implied * 100, 2)
            if avg_implied > 0
            else 0.0
        )

        return {
            "target_valuation": target_valuation,
            "peer_comparison": peer_comparison,
            "avg_peer_metrics": avg_metrics,
            "implied_value": implied_values,
            "avg_implied_value": round(avg_implied, 2),
            "premium_discount": premium_discount,
            "overall_premium_discount_pct": overall_premium,
            "current_price": current_price,
        }
