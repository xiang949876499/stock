"""事件驱动策略"""

from .base import AnalysisStrategy


class NewsStrategy(AnalysisStrategy):
    """新闻事件策略"""

    def get_prompt_template(self) -> str:
        return """
        分析 {stock_name}({stock_code}) 的新闻事件：

        ## 新闻
        {news}

        ## 要求
        1. 分析新闻的利好/利空性质
        2. 评估新闻的影响程度
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


class HotStrategy(AnalysisStrategy):
    """热点题材策略"""

    def get_prompt_template(self) -> str:
        return """
        分析 {stock_name}({stock_code}) 的热点题材：

        ## 要求
        1. 分析当前市场热点
        2. 判断股票与热点的关联度
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
