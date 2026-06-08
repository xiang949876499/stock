"""a-share-skill 策略适配器"""

import os
import sys
from typing import Optional

from src.analysis.strategies.base import AnalysisStrategy
from src.infra.logger import get_logger

logger = get_logger("ashare_strategies")

# a-share-skill 策略路径
STRATEGIES_PATH = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'a-share-skill')


class AShareMACDTrendResonance(AnalysisStrategy):
    """MACD 趋势共振选股策略"""

    def get_prompt_template(self) -> str:
        return """
        使用 MACD 趋势共振策略分析 {stock_name}({stock_code})：

        ## 策略逻辑
        1. 均线定方向：60日线方向与股价相对位置
        2. MACD 定节奏：0轴位置、金叉/红柱、日线与60分钟共振

        ## 输出要求
        - 候选分级：A/B/C/D 四档
        - 触发条件
        - 失效条件
        - 风控提示
        - 评分（0-100）
        - 动作：EXECUTE/LIGHT/OBSERVE/AVOID

        请以 JSON 格式输出：
        {{
            "score": 85,
            "signal": "buy",
            "trend": "bullish",
            "grade": "A",
            "action": "EXECUTE",
            "reason": "分析理由",
            "trigger": "触发条件",
            "invalidation": "失效条件",
            "risk": "风控提示"
        }}
        """

    def parse_result(self, raw: str) -> dict:
        import json
        try:
            return json.loads(raw)
        except:
            return {
                "score": 50,
                "signal": "hold",
                "trend": "neutral",
                "grade": "C",
                "action": "OBSERVE",
                "reason": "解析失败"
            }


class AShareMACDSecondGoldenCross(AnalysisStrategy):
    """MACD 底背离 + 零轴下二次金叉策略"""

    def get_prompt_template(self) -> str:
        return """
        使用 MACD 二次金叉策略分析 {stock_name}({stock_code})：

        ## 策略逻辑
        1. 识别第一脚/第二脚/水下二次金叉结构
        2. 三档决策：观察/试错/放弃

        ## 盘中检查单（10条）
        - 7条以上可试错

        ## 输出要求
        - 决策档位
        - 触发条件
        - 入场方式
        - 失效信号
        - 止损位
        - 仓位建议

        请以 JSON 格式输出：
        {{
            "score": 75,
            "signal": "buy",
            "trend": "neutral",
            "decision": "试错",
            "reason": "分析理由",
            "entry": "入场方式",
            "stop_loss": "止损位",
            "position": "仓位建议"
        }}
        """

    def parse_result(self, raw: str) -> dict:
        import json
        try:
            return json.loads(raw)
        except:
            return {
                "score": 50,
                "signal": "hold",
                "trend": "neutral",
                "decision": "观察",
                "reason": "解析失败"
            }


class AShareTuigeShortline(AnalysisStrategy):
    """退哥短线场景化交易决策策略"""

    def get_prompt_template(self) -> str:
        return """
        使用退哥短线策略分析 {stock_name}({stock_code})：

        ## 策略逻辑
        1. market-regime -> stock-selection -> 场景模块 -> exit/discipline
        2. 场景：趋势回踩/涨停后回调/连板接力/洗盘末端确认

        ## 输出要求
        - 场景分类
        - trigger（触发条件）
        - invalidation（失效条件）
        - risk（风险）
        - position_grade（仓位等级）

        请以 JSON 格式输出：
        {{
            "score": 80,
            "signal": "buy",
            "trend": "bullish",
            "scenario": "趋势回踩",
            "trigger": "触发条件",
            "invalidation": "失效条件",
            "risk": "风险提示",
            "position_grade": "B",
            "reason": "分析理由"
        }}
        """

    def parse_result(self, raw: str) -> dict:
        import json
        try:
            return json.loads(raw)
        except:
            return {
                "score": 50,
                "signal": "hold",
                "trend": "neutral",
                "scenario": "未知",
                "reason": "解析失败"
            }


class AShareSwingDefensive(AnalysisStrategy):
    """主板多空摆动防御策略"""

    def get_prompt_template(self) -> str:
        return """
        使用主板摆动防御策略分析 {stock_name}({stock_code})：

        ## 策略逻辑
        1. 主板高成交额股票池
        2. 日线 trend_pullback 选股

        ## 输出要求
        - 买入参考（entry）
        - 卖出参考（exit）
        - 评分
        - 信号强度

        请以 JSON 格式输出：
        {{
            "score": 70,
            "signal": "hold",
            "trend": "neutral",
            "entry": "买入参考",
            "exit": "卖出参考",
            "reason": "分析理由"
        }}
        """

    def parse_result(self, raw: str) -> dict:
        import json
        try:
            return json.loads(raw)
        except:
            return {
                "score": 50,
                "signal": "hold",
                "trend": "neutral",
                "reason": "解析失败"
            }


# 注册 a-share-skill 策略
def register_ashare_strategies(registry: dict):
    """注册 a-share-skill 策略"""
    registry["macd_trend_resonance"] = AShareMACDTrendResonance()
    registry["macd_second_golden_cross"] = AShareMACDSecondGoldenCross()
    registry["tuige_shortline"] = AShareTuigeShortline()
    registry["swing_defensive"] = AShareSwingDefensive()

    logger.info("注册 a-share-skill 策略: 4 个")
