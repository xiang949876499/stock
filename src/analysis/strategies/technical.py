"""技术分析策略"""

from .base import AnalysisStrategy


class MACrossStrategy(AnalysisStrategy):
    """均线金叉策略"""

    def get_prompt_template(self) -> str:
        return """
        分析 {stock_name}({stock_code}) 的均线金叉情况：

        ## 数据
        - 5日均线: {ma5}
        - 10日均线: {ma10}
        - 20日均线: {ma20}
        - 60日均线: {ma60}
        - 当前价格: {current_price}

        ## 要求
        1. 判断是否形成金叉（短期均线上穿长期均线）
        2. 分析金叉的强度和可靠性
        3. 给出买卖建议和目标价位
        4. 提示风险点

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


class MACDStrategy(AnalysisStrategy):
    """MACD 策略"""

    def get_prompt_template(self) -> str:
        return """
        分析 {stock_name}({stock_code}) 的 MACD 情况：

        ## 数据
        - MACD: {macd}
        - MACD Signal: {macd_signal}
        - MACD Hist: {macd_hist}

        ## 要求
        1. 判断 MACD 金叉/死叉
        2. 分析 MACD 柱状图变化
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
