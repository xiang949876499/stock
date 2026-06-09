"""公司简介插件（一页纸概述）

生成公司一页纸研究报告，包含公司概况、业务描述、财务摘要、估值和风险。
"""

from typing import Any, Dict, List

from src.plugins.base import AnalysisPlugin


# 模拟公司概况数据（实际生产中应从数据源获取）
MOCK_COMPANY_PROFILES: Dict[str, Dict[str, Any]] = {
    "600519": {
        "name": "贵州茅台",
        "industry": "白酒",
        "sector": "消费品",
        "founded": 1999,
        "headquarters": "贵州省仁怀市",
        "employees": 32000,
        "website": "www.moutaichina.com",
        "business_description": (
            "贵州茅台是中国最知名的白酒企业，主营茅台酒及系列产品的生产与销售。"
            "公司拥有独特的酱香型白酒酿造工艺，产品具有极强的品牌溢价能力。"
            "茅台酒被誉为国酒，在高端白酒市场占据主导地位。"
        ),
        "competitive_advantages": [
            "品牌护城河深厚，品牌价值位列白酒行业第一",
            "独特的酱香型酿造工艺，具有不可复制性",
            "产品定价能力强，毛利率超过 90%",
            "经销商渠道稳固，终端需求旺盛",
        ],
        "key_products": ["飞天茅台", "茅台王子酒", "茅台迎宾酒", "赖茅"],
    },
}


def _format_yuan(value: float) -> str:
    """将金额格式化为亿元"""
    yi = value / 1e8
    return f"{yi:.2f}亿元"


def _format_pct(value: float) -> str:
    """将小数格式化为百分比"""
    return f"{value * 100:.2f}%"


def _build_company_overview(
    symbol: str, stock_data: Dict[str, Any]
) -> Dict[str, Any]:
    """构建公司概况"""
    profile = MOCK_COMPANY_PROFILES.get(symbol, {})
    return {
        "name": profile.get("name", stock_data.get("name", symbol)),
        "symbol": symbol,
        "industry": profile.get("industry", stock_data.get("industry", "未知")),
        "sector": profile.get("sector", "未知"),
        "founded": profile.get("founded", ""),
        "headquarters": profile.get("headquarters", ""),
        "employees": profile.get("employees", ""),
        "website": profile.get("website", ""),
    }


def _build_business_description(
    symbol: str, stock_data: Dict[str, Any]
) -> Dict[str, Any]:
    """构建业务描述"""
    profile = MOCK_COMPANY_PROFILES.get(symbol, {})
    return {
        "description": profile.get(
            "business_description",
            stock_data.get("business_description", "暂无业务描述"),
        ),
        "key_products": profile.get("key_products", []),
        "competitive_advantages": profile.get("competitive_advantages", []),
    }


def _build_financial_summary(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """构建财务摘要"""
    revenue = float(stock_data.get("revenue", 0))
    net_profit = float(stock_data.get("net_profit", 0))
    eps = float(stock_data.get("eps", 0))
    roe = float(stock_data.get("roe", 0))
    gross_margin = float(stock_data.get("gross_margin", 0))
    net_margin = float(stock_data.get("net_margin", 0))
    total_assets = float(stock_data.get("total_assets", 0))
    total_liabilities = float(stock_data.get("total_liabilities", 0))

    debt_to_equity = 0.0
    if total_assets > 0 and total_liabilities >= 0:
        equity = total_assets - total_liabilities
        if equity > 0:
            debt_to_equity = total_liabilities / equity

    return {
        "revenue": _format_yuan(revenue) if revenue > 0 else "N/A",
        "net_profit": _format_yuan(net_profit) if net_profit > 0 else "N/A",
        "eps": round(eps, 2),
        "roe": _format_pct(roe),
        "gross_margin": _format_pct(gross_margin),
        "net_margin": _format_pct(net_margin),
        "debt_to_equity": round(debt_to_equity, 2),
    }


def _build_valuation_summary(stock_data: Dict[str, Any]) -> Dict[str, Any]:
    """构建估值摘要"""
    current_price = float(stock_data.get("current_price", 0))
    pe_ratio = float(stock_data.get("pe_ratio", 0))
    pb_ratio = float(stock_data.get("pb_ratio", 0))
    ps_ratio = float(stock_data.get("ps_ratio", 0))
    market_cap = float(stock_data.get("market_cap", 0))

    return {
        "current_price": current_price,
        "pe_ratio": round(pe_ratio, 2),
        "pb_ratio": round(pb_ratio, 2),
        "ps_ratio": round(ps_ratio, 2),
        "market_cap": _format_yuan(market_cap) if market_cap > 0 else "N/A",
    }


def _identify_risks(stock_data: Dict[str, Any]) -> List[str]:
    """识别公司风险"""
    risks: List[str] = []

    roe = float(stock_data.get("roe", 0))
    net_margin = float(stock_data.get("net_margin", 0))
    gross_margin = float(stock_data.get("gross_margin", 0))
    total_liabilities = float(stock_data.get("total_liabilities", 0))
    total_assets = float(stock_data.get("total_assets", 0))
    pe_ratio = float(stock_data.get("pe_ratio", 0))

    if roe < 0.10:
        risks.append(f"ROE 偏低（{_format_pct(roe)}），资本回报效率不高")

    if net_margin < 0.10:
        risks.append(f"净利率偏低（{_format_pct(net_margin)}），盈利能力有待提升")

    if gross_margin < 0.30:
        risks.append(f"毛利率偏低（{_format_pct(gross_margin)}），可能面临成本压力")

    if total_assets > 0:
        debt_ratio = total_liabilities / total_assets
        if debt_ratio > 0.60:
            risks.append(
                f"资产负债率偏高（{debt_ratio * 100:.1f}%），财务杠杆较大"
            )

    if pe_ratio > 50:
        risks.append(f"PE 估值偏高（{pe_ratio:.1f}），存在估值回调风险")

    if not risks:
        risks.append("暂未发现明显风险因素")

    return risks


class OnePagerPlugin(AnalysisPlugin):
    """公司简介一页纸插件"""

    @property
    def name(self) -> str:
        return "company_one_pager"

    @property
    def description(self) -> str:
        return "公司一页纸概述 - 生成公司概况、业务描述、财务摘要、估值和风险的一页纸报告"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "symbol": {
                "type": "str",
                "default": "",
                "description": "股票代码",
            },
            "include_financials": {
                "type": "bool",
                "default": True,
                "description": "是否包含财务摘要",
            },
            "include_peers": {
                "type": "bool",
                "default": False,
                "description": "是否包含同行业对比",
            },
        }

    async def execute(
        self, stock_data: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行公司简介生成

        Args:
            stock_data: 股票数据
            params: 参数，包含 symbol, include_financials, include_peers

        Returns:
            公司一页纸报告
        """
        symbol = params.get("symbol", stock_data.get("symbol", ""))
        include_financials = params.get("include_financials", True)
        include_peers = params.get("include_peers", False)

        # 公司概况
        overview = _build_company_overview(symbol, stock_data)

        # 业务描述
        business = _build_business_description(symbol, stock_data)

        # 财务摘要
        financials = None
        if include_financials:
            financials = _build_financial_summary(stock_data)

        # 估值摘要
        valuation = _build_valuation_summary(stock_data)

        # 风险识别
        risks = _identify_risks(stock_data)

        result: Dict[str, Any] = {
            "overview": overview,
            "business": business,
            "valuation": valuation,
            "risks": risks,
        }

        if financials is not None:
            result["financial_summary"] = financials

        if include_peers:
            result["peers_note"] = "同行业对比数据请使用 comparable_analysis 插件获取"

        return result
