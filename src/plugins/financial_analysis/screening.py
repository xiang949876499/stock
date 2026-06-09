"""股票筛选插件

基于多维度指标筛选股票，支持 PE、ROE、市值、股息率等多个财务指标的 min/max 条件过滤，
并计算综合评分用于排序。
"""

from typing import Any, Dict, List

from src.plugins.base import AnalysisPlugin


# 模拟股票池数据
MOCK_STOCK_UNIVERSE: Dict[str, List[Dict[str, Any]]] = {
    "hs300": [
        {
            "symbol": "600519",
            "name": "贵州茅台",
            "pe_ratio": 30.5,
            "pb_ratio": 10.2,
            "roe": 0.32,
            "market_cap": 22000.0,
            "dividend_yield": 0.015,
            "revenue_growth": 0.16,
        },
        {
            "symbol": "000858",
            "name": "五粮液",
            "pe_ratio": 22.3,
            "pb_ratio": 6.5,
            "roe": 0.28,
            "market_cap": 8000.0,
            "dividend_yield": 0.020,
            "revenue_growth": 0.12,
        },
        {
            "symbol": "601318",
            "name": "中国平安",
            "pe_ratio": 9.8,
            "pb_ratio": 1.1,
            "roe": 0.16,
            "market_cap": 9500.0,
            "dividend_yield": 0.035,
            "revenue_growth": 0.05,
        },
        {
            "symbol": "000333",
            "name": "美的集团",
            "pe_ratio": 12.5,
            "pb_ratio": 3.2,
            "roe": 0.25,
            "market_cap": 4500.0,
            "dividend_yield": 0.028,
            "revenue_growth": 0.08,
        },
        {
            "symbol": "600036",
            "name": "招商银行",
            "pe_ratio": 7.2,
            "pb_ratio": 1.0,
            "roe": 0.17,
            "market_cap": 11000.0,
            "dividend_yield": 0.040,
            "revenue_growth": 0.03,
        },
        {
            "symbol": "002714",
            "name": "牧原股份",
            "pe_ratio": 45.0,
            "pb_ratio": 5.8,
            "roe": 0.12,
            "market_cap": 3200.0,
            "dividend_yield": 0.005,
            "revenue_growth": 0.25,
        },
        {
            "symbol": "601012",
            "name": "隆基绿能",
            "pe_ratio": 18.6,
            "pb_ratio": 3.5,
            "roe": 0.20,
            "market_cap": 2800.0,
            "dividend_yield": 0.010,
            "revenue_growth": 0.30,
        },
        {
            "symbol": "000001",
            "name": "平安银行",
            "pe_ratio": 5.5,
            "pb_ratio": 0.6,
            "roe": 0.11,
            "market_cap": 2500.0,
            "dividend_yield": 0.045,
            "revenue_growth": 0.02,
        },
        {
            "symbol": "600900",
            "name": "长江电力",
            "pe_ratio": 20.1,
            "pb_ratio": 3.8,
            "roe": 0.15,
            "market_cap": 5800.0,
            "dividend_yield": 0.038,
            "revenue_growth": 0.04,
        },
        {
            "symbol": "002304",
            "name": "洋河股份",
            "pe_ratio": 15.8,
            "pb_ratio": 4.0,
            "roe": 0.22,
            "market_cap": 2200.0,
            "dividend_yield": 0.025,
            "revenue_growth": 0.10,
        },
    ],
}

# 综合评分权重：指标 -> (权重, 是否越高越好)
SCORING_WEIGHTS: Dict[str, tuple] = {
    "pe_ratio": (0.20, False),       # PE 越低越好
    "roe": (0.25, True),             # ROE 越高越好
    "dividend_yield": (0.15, True),  # 股息率越高越好
    "revenue_growth": (0.20, True),  # 营收增长越高越好
    "pb_ratio": (0.10, False),       # PB 越低越好
    "market_cap": (0.10, True),      # 市值越大（流动性越好）
}


def _compute_score(stock: Dict[str, Any], universe: List[Dict[str, Any]]) -> float:
    """计算单只股票的综合评分（0-100）

    将每项指标在 universe 内做 min-max 归一化，再按权重加权求和。
    """
    score = 0.0
    for metric, (weight, higher_better) in SCORING_WEIGHTS.items():
        values = [s.get(metric, 0) for s in universe]
        min_val = min(values)
        max_val = max(values)
        val = stock.get(metric, 0)

        if max_val == min_val:
            normalized = 0.5
        elif higher_better:
            normalized = (val - min_val) / (max_val - min_val)
        else:
            normalized = (max_val - val) / (max_val - min_val)

        score += weight * normalized

    return round(score * 100, 2)


def _apply_filters(
    stocks: List[Dict[str, Any]],
    filters: Dict[str, Dict[str, float]],
) -> List[Dict[str, Any]]:
    """应用筛选条件

    Args:
        stocks: 股票列表
        filters: 筛选条件，格式 {指标名: {"min": ..., "max": ...}}

    Returns:
        通过筛选的股票列表
    """
    result = []
    for stock in stocks:
        passed = True
        for metric, conditions in filters.items():
            val = stock.get(metric)
            if val is None:
                passed = False
                break
            if "min" in conditions and val < conditions["min"]:
                passed = False
                break
            if "max" in conditions and val > conditions["max"]:
                passed = False
                break
        if passed:
            result.append(stock)
    return result


class StockScreeningPlugin(AnalysisPlugin):
    """股票筛选插件"""

    @property
    def name(self) -> str:
        return "stock_screening"

    @property
    def description(self) -> str:
        return "股票筛选 - 基于多维度财务指标筛选股票池，支持自定义条件和综合评分排序"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "universe": {
                "type": "str",
                "default": "hs300",
                "description": "股票池名称，如 hs300",
            },
            "filters": {
                "type": "Dict[str, Dict[str, float]]",
                "default": {},
                "description": "筛选条件，格式: {指标名: {min: ..., max: ...}}",
            },
            "sort_by": {
                "type": "str",
                "default": "score",
                "description": "排序字段，默认按综合评分排序",
            },
            "limit": {
                "type": "int",
                "default": 10,
                "description": "返回结果数量上限",
            },
        }

    async def execute(
        self, stock_data: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行股票筛选

        Args:
            stock_data: 未使用（筛选基于内置股票池）
            params: 包含 universe, filters, sort_by, limit

        Returns:
            筛选结果
        """
        universe_name: str = params.get("universe", "hs300")
        filters: Dict[str, Dict[str, float]] = params.get("filters", {})
        sort_by: str = params.get("sort_by", "score")
        limit: int = params.get("limit", 10)

        # 获取股票池
        universe = MOCK_STOCK_UNIVERSE.get(universe_name, [])

        # 应用筛选条件
        filtered = _apply_filters(universe, filters)

        # 计算综合评分
        scored: List[Dict[str, Any]] = []
        for stock in filtered:
            entry = dict(stock)
            entry["score"] = _compute_score(stock, universe)
            scored.append(entry)

        # 排序
        if sort_by == "score":
            scored.sort(key=lambda s: s["score"], reverse=True)
        elif sort_by in scored[0] if scored else {}:
            scored.sort(key=lambda s: s.get(sort_by, 0), reverse=True)

        # 限制结果数量
        results = scored[:limit]

        return {
            "results": results,
            "total_count": len(filtered),
            "filters_applied": filters,
        }
