"""综合分析插件 - 集成 Stock-Analysis-Skill

100 分评分系统，包含 MA/MACD/RSI/量能/乖离率/支撑位 6 维度分析。
支持 A 股、港股、美股。
"""

from typing import Dict, Any, List

from src.plugins.base import AnalysisPlugin
from src.plugins.financial_analysis.technical_indicators import (
    calc_ma,
    calc_macd,
    calc_rsi,
    calc_volume_analysis,
    calc_bias,
    calc_support,
    calc_trend_score,
)


class ComprehensiveAnalysisPlugin(AnalysisPlugin):
    """综合分析插件 - 100 分评分系统"""

    @property
    def name(self) -> str:
        return "comprehensive_analysis"

    @property
    def description(self) -> str:
        return "综合分析 - 100 分评分系统，包含 MA/MACD/RSI/量能/乖离率/支撑位分析"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "symbol": {
                "type": "str",
                "description": "股票代码",
            },
            "days": {
                "type": "int",
                "default": 120,
                "description": "历史天数",
            },
        }

    async def execute(
        self, stock_data: Any, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行综合分析

        Args:
            stock_data: 股票数据，需包含 ohlcv K 线数据
            params: 分析参数

        Returns:
            包含技术指标和评分的综合分析结果
        """
        # 从 stock_data 获取 K 线数据
        ohlcv = stock_data.get("ohlcv", [])
        if not ohlcv or len(ohlcv) < 10:
            return {"error": "数据不足，至少需要 10 条 K 线数据"}

        closes = [bar["close"] for bar in ohlcv if bar.get("close") is not None]
        volumes = [bar["volume"] for bar in ohlcv if bar.get("volume") is not None]

        if len(closes) < 10:
            return {"error": "有效收盘价数据不足"}

        # 计算技术指标
        ma = calc_ma(closes, [5, 10, 20, 60])
        macd = calc_macd(closes)
        rsi = calc_rsi(closes, [6, 12, 24])
        vol = calc_volume_analysis(volumes, closes)
        bias = calc_bias(closes, ma)
        support = calc_support(closes, ma)
        score = calc_trend_score(ma, macd, rsi, vol, bias, support)

        return {
            "symbol": stock_data.get("symbol"),
            "name": stock_data.get("name"),
            "current_price": closes[-1] if closes else None,
            "indicators": {
                "ma": ma,
                "macd": macd,
                "rsi": rsi,
                "volume": vol,
                "bias": bias,
                "support": support,
            },
            "trend_score": score,
            "signal": score.get("signal"),
            "signal_cn": score.get("signal_cn"),
        }
