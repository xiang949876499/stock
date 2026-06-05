"""基本面策略"""

from .base import AnalysisStrategy


class GrowthStrategy(AnalysisStrategy):
    """成长质量策略"""

    def get_prompt_template(self) -> str:
        return """
        分析 {stock_name}({stock_code}) 的成长质量：

        ## 财务数据
        - 营收增长率: {revenue_growth}
        - 净利润增长率: {profit_growth}
        - ROE: {roe}
        - PE: {pe}

        ## 要求
        1. 分析公司的成长性
        2. 评估盈利能力
        3. 给出投资建议

        请以 JSON 格式输出：
        {{
            "score": 85,
            "signal": "buy",
            "trend": "bullish",
            "reason": "分析理由"
        }}
        """

    def parse_result(self, raw: str) -> dict:
        import json
        try:
            return json.loads(raw)
        except:
            return {"score": 50, "signal": "hold", "trend": "neutral", "reason": "解析失败"}


class ValueStrategy(AnalysisStrategy):
    """价值投资策略"""

    def get_prompt_template(self) -> str:
        return """
        分析 {stock_name}({stock_code}) 的投资价值：

        ## 财务数据
        - PE: {pe}
        - PB: {pb}
        - 股息率: {dividend_yield}

        ## 要求
        1. 分析估值水平
        2. 评估安全边际
        3. 给出投资建议

        请以 JSON 格式输出：
        {{
            "score": 85,
            "signal": "buy",
            "trend": "bullish",
            "reason": "分析理由"
        }}
        """

    def parse_result(self, raw: str) -> dict:
        import json
        try:
            return json.loads(raw)
        except:
            return {"score": 50, "signal": "hold", "trend": "neutral", "reason": "解析失败"}
