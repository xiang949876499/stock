"""股票推荐策略"""

from typing import Optional
import pandas as pd

from src.data.models import Market
from src.data.service import DataService
from src.infra.logger import get_logger

logger = get_logger("stock_picker")


class StockPicker:
    """股票推荐器"""

    def __init__(self, data_service: Optional[DataService] = None):
        self.data_service = data_service or DataService()

    async def recommend(
        self,
        market: Market = Market.A,
        top_n: int = 10,
        strategy: str = "comprehensive",
    ) -> list[dict]:
        """推荐股票"""
        try:
            # 获取股票列表
            stocks = []
            for symbol, info in self.data_service.catalog.mapping.items():
                if info.get("market") == market.value:
                    stocks.append({
                        "symbol": symbol,
                        "name": info.get("name", ""),
                        "market": market.value,
                    })

            if not stocks:
                logger.warning("没有找到股票")
                return []

            # 计算评分
            scored_stocks = []
            for stock in stocks[:50]:  # 限制数量避免太慢
                try:
                    score = await self._calculate_score(stock["symbol"], market, strategy)
                    stock["score"] = score
                    scored_stocks.append(stock)
                except Exception as e:
                    logger.warning(f"计算 {stock['symbol']} 评分失败: {e}")
                    continue

            # 按评分排序
            scored_stocks.sort(key=lambda x: x["score"], reverse=True)

            # 返回 Top N
            return scored_stocks[:top_n]

        except Exception as e:
            logger.error(f"推荐股票失败: {e}")
            return []

    async def _calculate_score(
        self,
        symbol: str,
        market: Market,
        strategy: str,
    ) -> float:
        """计算股票评分"""
        try:
            # 获取技术指标
            indicators = await self.data_service.get_technical_indicators(symbol, market)

            score = 50.0  # 基础分

            # 均线评分
            if indicators.ma5 > indicators.ma10 > indicators.ma20:
                score += 10  # 多头排列
            elif indicators.ma5 < indicators.ma10 < indicators.ma20:
                score -= 10  # 空头排列

            # MACD 评分
            if indicators.macd > indicators.macd_signal:
                score += 10  # MACD 金叉
            if indicators.macd_hist > 0:
                score += 5  # MACD 柱状图为正

            # RSI 评分
            if 30 < indicators.rsi_6 < 70:
                score += 5  # RSI 正常区间
            elif indicators.rsi_6 < 30:
                score += 10  # 超卖，可能反弹
            elif indicators.rsi_6 > 70:
                score -= 5  # 超买，注意风险

            # KDJ 评分
            if indicators.kdj_k > indicators.kdj_d:
                score += 5  # KDJ 金叉

            # 布林带评分（使用 boll_middle 判断趋势）
            if indicators.boll_middle > 0:
                score += 5  # 有布林带数据

            return min(max(score, 0), 100)  # 限制在 0-100

        except Exception as e:
            logger.warning(f"计算 {symbol} 评分失败: {e}")
            return 50.0


async def get_stock_recommendations(
    market: str = "A",
    top_n: int = 10,
    strategy: str = "comprehensive",
) -> list[dict]:
    """获取股票推荐（便捷函数）"""
    picker = StockPicker()
    market_enum = Market(market)
    return await picker.recommend(market_enum, top_n, strategy)
