"""趋势策略"""

from .base import AnalysisStrategy


class TrendStrategy(AnalysisStrategy):
    """多头趋势策略"""

    def get_prompt_template(self) -> str:
        return """
        分析 {stock_name}({stock_code}) 的趋势：

        ## 数据
        - 当前价格: {current_price}
        - MA5: {ma5}
        - MA10: {ma10}
        - MA20: {ma20}
        - MA60: {ma60}

        ## 要求
        1. 判断趋势方向
        2. 分析趋势强度
        3. 给出买卖建议

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


class WaveStrategy(AnalysisStrategy):
    """波浪理论策略"""

    def get_prompt_template(self) -> str:
        return """
        分析 {stock_name}({stock_code}) 的波浪形态：

        ## 要求
        1. 识别当前波浪位置
        2. 预测下一波浪方向
        3. 给出买卖建议

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


class ChanStrategy(AnalysisStrategy):
    """缠论策略"""

    def get_prompt_template(self) -> str:
        return """
        分析 {stock_name}({stock_code}) 的缠论形态：

        ## 要求
        1. 识别中枢位置
        2. 判断买卖点
        3. 给出操作建议

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
