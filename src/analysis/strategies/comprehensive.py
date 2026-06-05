"""综合分析策略"""

from .base import AnalysisStrategy


class ComprehensiveStrategy(AnalysisStrategy):
    """综合分析策略"""

    def get_prompt_template(self) -> str:
        return """
        你是一个专业的股票分析师，请对 {stock_name}({stock_code}) 进行综合分析。

        ## 当前数据
        - 当前价格: {current_price}
        - 5日均线: {ma5}
        - 10日均线: {ma10}
        - 20日均线: {ma20}
        - 60日均线: {ma60}
        - MACD: {macd}
        - MACD Signal: {macd_signal}
        - MACD Hist: {macd_hist}
        - RSI(6): {rsi_6}
        - RSI(12): {rsi_12}
        - KDJ-K: {kdj_k}
        - KDJ-D: {kdj_d}
        - KDJ-J: {kdj_j}

        ## 分析要求
        1. **技术面分析**
           - 均线系统：判断多头/空头排列
           - MACD：判断金叉/死叉、柱状图变化
           - RSI：判断超买/超卖
           - KDJ：判断金叉/死叉

        2. **趋势判断**
           - 短期趋势（5-10日）
           - 中期趋势（20-60日）
           - 趋势强度

        3. **买卖建议**
           - 信号类型：buy/sell/hold
           - 目标价位
           - 止损价位

        4. **风险提示**
           - 主要风险点
           - 注意事项

        请以 JSON 格式输出分析结果：
        {{
            "score": 85,
            "signal": "buy",
            "trend": "bullish",
            "target_price": 1900.0,
            "stop_loss": 1750.0,
            "reason": "详细分析理由",
            "risks": ["风险点1", "风险点2"],
            "technical_summary": "技术面总结"
        }}
        """

    def parse_result(self, raw: str) -> dict:
        import json
        try:
            # 尝试直接解析
            return json.loads(raw)
        except json.JSONDecodeError:
            # 尝试提取 JSON 部分
            import re
            json_match = re.search(r'\{[\s\S]*\}', raw)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass

            # 返回默认值
            return {
                "score": 50,
                "signal": "hold",
                "trend": "neutral",
                "reason": raw if raw else "分析失败",
                "risks": [],
                "technical_summary": ""
            }
