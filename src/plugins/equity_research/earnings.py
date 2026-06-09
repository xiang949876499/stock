"""财报分析插件

分析公司财务报告，提取关键财务指标，识别亮点与风险，生成结构化分析报告。
"""

from typing import Any, Dict, List

from src.plugins.base import AnalysisPlugin


# ---------------------------------------------------------------------------
# 阈值 / 基准常量
# ---------------------------------------------------------------------------

# 毛利率阈值
GROSS_MARGIN_HIGH = 0.60
GROSS_MARGIN_MID = 0.40

# 净利率阈值
NET_MARGIN_HIGH = 0.20
NET_MARGIN_MID = 0.10

# ROE 阈值
ROE_HIGH = 0.20
ROE_MID = 0.10

# 经营现金流 / 净利润比率阈值
OCF_NP_RATIO_HEALTHY = 1.0
OCF_NP_RATIO_WARN = 0.5


def _format_yuan(value: float) -> str:
    """将金额格式化为亿元字符串"""
    yi = value / 1e8
    return f"{yi:.2f}亿元"


def _format_pct(value: float) -> str:
    """将小数格式化为百分比字符串"""
    return f"{value * 100:.2f}%"


# ---------------------------------------------------------------------------
# 分析逻辑
# ---------------------------------------------------------------------------

def _extract_financial_metrics(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """提取并格式化关键财务指标"""
    revenue = float(stock_data.get("revenue", 0))
    net_profit = float(stock_data.get("net_profit", 0))
    eps = float(stock_data.get("eps", 0))
    roe = float(stock_data.get("roe", 0))
    gross_margin = float(stock_data.get("gross_margin", 0))
    net_margin = float(stock_data.get("net_margin", 0))
    operating_cash_flow = float(stock_data.get("operating_cash_flow", 0))

    return {
        "revenue": revenue,
        "net_profit": net_profit,
        "eps": eps,
        "roe": roe,
        "gross_margin": gross_margin,
        "net_margin": net_margin,
        "operating_cash_flow": operating_cash_flow,
        "ocf_to_np_ratio": (
            operating_cash_flow / net_profit if net_profit > 0 else 0
        ),
    }


def _identify_highlights(
    metrics: Dict[str, Any], focus_areas: List[str]
) -> List[str]:
    """识别财报亮点"""
    highlights: List[str] = []

    # 盈利能力亮点
    if "margins" in focus_areas or not focus_areas:
        gm = metrics["gross_margin"]
        if gm >= GROSS_MARGIN_HIGH:
            highlights.append(
                f"毛利率 {_format_pct(gm)} 处于高位，显示强大的定价权和竞争优势"
            )
        nm = metrics["net_margin"]
        if nm >= NET_MARGIN_HIGH:
            highlights.append(
                f"净利率 {_format_pct(nm)} 优秀，盈利能力突出"
            )

    # ROE 亮点
    roe = metrics["roe"]
    if roe >= ROE_HIGH:
        highlights.append(
            f"ROE {_format_pct(roe)} 超过 {_format_pct(ROE_HIGH)}，资本回报率高"
        )

    # 现金流亮点
    if "cash_flow" in focus_areas or not focus_areas:
        ocf = metrics["operating_cash_flow"]
        np_ = metrics["net_profit"]
        if np_ > 0 and ocf / np_ >= OCF_NP_RATIO_HEALTHY:
            highlights.append(
                f"经营现金流/净利润 = {ocf / np_:.2f}，"
                "盈利质量高，现金流充沛"
            )

    # 营收亮点
    if "revenue" in focus_areas or not focus_areas:
        rev = metrics["revenue"]
        if rev > 0:
            highlights.append(f"营收 {_format_yuan(rev)}")

    # EPS 亮点
    if metrics["eps"] > 0:
        highlights.append(f"每股收益 {metrics['eps']:.2f} 元")

    return highlights


def _identify_risks(
    metrics: Dict[str, Any], focus_areas: List[str]
) -> List[str]:
    """识别财报风险"""
    risks: List[str] = []

    # 毛利率风险
    gm = metrics["gross_margin"]
    if gm < GROSS_MARGIN_MID:
        risks.append(
            f"毛利率 {_format_pct(gm)} 偏低，可能面临成本压力或竞争加剧"
        )

    # 净利率风险
    nm = metrics["net_margin"]
    if nm < NET_MARGIN_MID:
        risks.append(
            f"净利率 {_format_pct(nm)} 偏低，盈利能力有待改善"
        )

    # ROE 风险
    roe = metrics["roe"]
    if roe < ROE_MID:
        risks.append(
            f"ROE {_format_pct(roe)} 偏低，资本使用效率不高"
        )

    # 现金流风险
    if "cash_flow" in focus_areas or not focus_areas:
        ocf = metrics["operating_cash_flow"]
        np_ = metrics["net_profit"]
        if np_ > 0 and ocf / np_ < OCF_NP_RATIO_WARN:
            risks.append(
                f"经营现金流/净利润 = {ocf / np_:.2f}，"
                "盈利质量存疑，现金流与利润不匹配"
            )
        elif np_ > 0 and ocf < 0:
            risks.append("经营现金流为负，需关注公司经营可持续性")

    # 亏损风险
    if np_ < 0:
        risks.append("净利润为负，公司处于亏损状态")

    return risks


def _build_yoy_comparison(
    stock_data: Dict[str, Any], params: Dict[str, Any]
) -> Dict[str, Any]:
    """构建同比/环比对比数据

    当前为简化实现，返回基于 stock_data 中 present/previous 数据的对比。
    实际生产中应从数据库或 API 获取历史数据。
    """
    period = params.get("period", "")
    compare_with = params.get("compare_with", "")

    # 如果 stock_data 中包含对比数据，使用之
    prev_data = stock_data.get("previous_period", {})

    if prev_data:
        comparison: Dict[str, Any] = {}
        for key in ("revenue", "net_profit", "eps", "roe"):
            current = float(stock_data.get(key, 0))
            previous = float(prev_data.get(key, 0))
            if previous != 0:
                change_pct = (current - previous) / previous
            else:
                change_pct = 0.0
            comparison[key] = {
                "current": current,
                "previous": previous,
                "change_pct": round(change_pct, 4),
            }
        return comparison

    # 无历史数据时返回占位信息
    return {
        "period": period,
        "compare_with": compare_with,
        "note": "历史对比数据不可用，请提供 previous_period 数据以启用同比分析",
    }


def _generate_summary(
    name: str,
    period: str,
    metrics: Dict[str, Any],
    highlights: List[str],
    risks: List[str],
) -> str:
    """生成财报摘要文本"""
    parts: List[str] = []

    parts.append(f"【{name} {period} 财报分析摘要】")

    # 整体评价
    score = 0
    if metrics["gross_margin"] >= GROSS_MARGIN_HIGH:
        score += 1
    if metrics["net_margin"] >= NET_MARGIN_HIGH:
        score += 1
    if metrics["roe"] >= ROE_HIGH:
        score += 1
    ocf = metrics["operating_cash_flow"]
    np_ = metrics["net_profit"]
    if np_ > 0 and ocf / np_ >= OCF_NP_RATIO_HEALTHY:
        score += 1

    if score >= 3:
        parts.append("整体财务状况优秀，多项核心指标表现突出。")
    elif score >= 2:
        parts.append("整体财务状况良好，部分指标表现优异。")
    elif score >= 1:
        parts.append("财务表现中等，存在改善空间。")
    else:
        parts.append("财务表现较弱，需重点关注风险因素。")

    if highlights:
        parts.append(f"亮点方面：{'；'.join(highlights[:3])}。")

    if risks:
        parts.append(f"风险方面：{'；'.join(risks[:3])}。")
    else:
        parts.append("未发现明显风险因素。")

    return "".join(parts)


# ---------------------------------------------------------------------------
# 插件类
# ---------------------------------------------------------------------------


class EarningsAnalysisPlugin(AnalysisPlugin):
    """财报分析插件"""

    @property
    def name(self) -> str:
        return "earnings_analysis"

    @property
    def description(self) -> str:
        return "财报分析 - 分析公司财报关键指标，识别亮点与风险，生成结构化分析报告"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "period": {
                "type": "str",
                "default": "",
                "description": "分析期间，如 2024Q3",
            },
            "compare_with": {
                "type": "str",
                "default": "",
                "description": "对比期间，如 2023Q3",
            },
            "focus_areas": {
                "type": "List[str]",
                "default": [],
                "description": "重点关注领域，如 ['revenue', 'margins', 'cash_flow']",
            },
        }

    async def execute(
        self, stock_data: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行财报分析

        Args:
            stock_data: 股票数据，需包含 revenue, net_profit, eps, roe,
                        gross_margin, net_margin, operating_cash_flow
            params: 分析参数，包含 period, compare_with, focus_areas

        Returns:
            财报分析结果，包含 summary, highlights, risks,
            financial_metrics, yoy_comparison
        """
        name = stock_data.get("name", stock_data.get("symbol", "未知"))
        period = params.get("period", "")
        focus_areas: List[str] = params.get("focus_areas", [])

        # 提取财务指标
        metrics = _extract_financial_metrics(stock_data)

        # 识别亮点与风险
        highlights = _identify_highlights(metrics, focus_areas)
        risks = _identify_risks(metrics, focus_areas)

        # 构建同比对比
        yoy_comparison = _build_yoy_comparison(stock_data, params)

        # 生成摘要
        summary = _generate_summary(name, period, metrics, highlights, risks)

        return {
            "summary": summary,
            "highlights": highlights,
            "risks": risks,
            "financial_metrics": metrics,
            "yoy_comparison": yoy_comparison,
        }
