"""股票推荐策略 - 两层筛选"""

from typing import Callable, Optional

from src.data.models import Market
from src.data.service import DataService
from src.infra.logger import get_logger

logger = get_logger("stock_picker")


class StockPicker:
    """股票推荐器

    两层筛选策略：
    1. 技术面快筛（全量，纯本地计算）→ Top 100
    2. AI 深度分析（Top 100）→ Top 10
    """

    def __init__(self, data_service: Optional[DataService] = None):
        self.data_service = data_service or DataService()

    async def recommend(
        self,
        market: Market = Market.A,
        top_n: int = 10,
        strategy: str = "comprehensive",
        use_ai_screen: bool = True,
        progress_callback: Optional[Callable[[str], None]] = None,
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

            logger.info(f"开始两层筛选: {len(stocks)} 只 {market.value} 股票")
            if progress_callback:
                progress_callback(f"开始技术快筛：共 {len(stocks)} 只 {market.value} 股")

            # ── 第一层：技术面快筛（全量）──
            quick_scored = await self._quick_screen(stocks, market, progress_callback)
            if not quick_scored:
                logger.warning("技术面快筛无结果")
                return []

            if not use_ai_screen:
                selected = quick_scored[:top_n]
                if progress_callback:
                    progress_callback(
                        f"技术快筛完成：{len(quick_scored)} 只有效候选，"
                        f"选取 Top {len(selected)} 进入交易决策"
                    )
                return selected

            # 取 Top 100 进入第二层
            candidates = quick_scored[:100]
            logger.info(f"第一层快筛完成: Top {len(candidates)} 进入 AI 分析")

            # ── 第二层：AI 深度分析（Top 100）──
            final_stocks = await self._ai_deep_screen(candidates, market, strategy, top_n)
            logger.info(f"两层筛选完成: 最终 Top {len(final_stocks)}")

            return final_stocks

        except Exception as e:
            logger.error(f"推荐股票失败: {e}")
            return []

    async def _quick_screen(
        self,
        stocks: list[dict],
        market: Market,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> list[dict]:
        """第一层：技术面快筛

        使用本地 parquet 数据计算基础技术指标，速度快。
        """
        scored_stocks = []
        processed = 0
        skipped = 0

        total = len(stocks)
        for index, stock in enumerate(stocks, 1):
            symbol = stock["symbol"]
            try:
                # 获取日线数据（优先从本地 parquet 加载）
                from datetime import date, timedelta
                end_date = date.today()
                start_date = end_date - timedelta(days=120)

                df = await self.data_service.get_daily(symbol, market, start_date, end_date)
                if df is None or df.empty or len(df) < 30:
                    skipped += 1
                    continue

                closes = df["close"].tolist()
                volumes = df["volume"].tolist()

                # 计算快筛评分
                score = self._calculate_quick_score(closes, volumes)
                stock["score"] = score
                scored_stocks.append(stock)
                processed += 1

            except Exception:
                skipped += 1
                continue
            finally:
                if progress_callback and (index % 500 == 0 or index == total):
                    progress_callback(
                        f"技术快筛进度：已检查 {index}/{total} 只，"
                        f"有效 {processed} 只，跳过 {skipped} 只"
                    )

        logger.info(f"技术面快筛: 处理 {processed}, 跳过 {skipped}")

        # 按评分排序
        scored_stocks.sort(key=lambda x: x["score"], reverse=True)
        return scored_stocks

    def _calculate_quick_score(self, closes: list[float], volumes: list[float]) -> float:
        """计算快筛评分（纯本地计算，无网络请求）"""
        from src.plugins.financial_analysis.technical_indicators import (
            calc_ma, calc_macd, calc_rsi, calc_volume_analysis,
        )

        score = 50.0  # 基础分

        # 均线评分
        try:
            ma_data = calc_ma(closes, [5, 10, 20, 60])
            if ma_data.get("ma_arrangement") == "bullish":
                score += 15  # 多头排列
            elif ma_data.get("ma_arrangement") == "bearish":
                score -= 10  # 空头排列

            # 价格在均线上方
            if ma_data.get("ma5_trend") == "above":
                score += 3
            if ma_data.get("ma20_trend") == "above":
                score += 3
        except Exception:
            pass

        # MACD 评分
        try:
            macd_data = calc_macd(closes)
            if macd_data.get("cross_signal") == "golden_cross":
                score += 10  # 金叉
            elif macd_data.get("cross_signal") == "death_cross":
                score -= 8  # 死叉
            if macd_data.get("above_zero"):
                score += 5  # DIF/DEA 在零轴上方
        except Exception:
            pass

        # RSI 评分
        try:
            rsi_data = calc_rsi(closes, [6, 12])
            rsi12 = rsi_data.get("rsi12")
            if rsi12 is not None:
                if 30 < rsi12 < 70:
                    score += 5  # 正常区间
                elif rsi12 <= 30:
                    score += 10  # 超卖反弹机会
                elif rsi12 >= 70:
                    score -= 5  # 超买风险
        except Exception:
            pass

        # 量能评分
        try:
            vol_data = calc_volume_analysis(volumes, closes)
            if vol_data.get("price_vol_relation") == "bullish_volume":
                score += 8  # 价升量增
            elif vol_data.get("price_vol_relation") == "bearish_volume":
                score -= 5  # 价跌量增
        except Exception:
            pass

        return min(max(score, 0), 100)

    async def _ai_deep_screen(
        self,
        candidates: list[dict],
        market: Market,
        strategy: str,
        top_n: int,
    ) -> list[dict]:
        """第二层：AI 深度分析

        对快筛 Top 100 候选进行 AI 分析，返回最终 Top N。
        """
        try:
            from src.config import get_settings
            from src.analysis.ai.factory import AIModelFactory

            config = get_settings()
            ai_adapter = AIModelFactory.create(config)

            if not ai_adapter:
                logger.warning("AI 未配置，仅返回技术面评分结果")
                return candidates[:top_n]

            from src.analysis.service import AnalysisService
            service = AnalysisService(ai_adapter)

            scored_stocks = []
            for stock in candidates:
                symbol = stock["symbol"]
                try:
                    result = await service.analyze_stock(symbol, strategy)
                    # 综合评分：技术面 40% + AI 60%
                    tech_score = stock.get("score", 50)
                    combined_score = tech_score * 0.4 + result.score * 0.6
                    stock["score"] = round(combined_score, 1)
                    stock["ai_score"] = result.score
                    stock["ai_signal"] = result.signal
                    stock["ai_trend"] = result.trend
                    scored_stocks.append(stock)
                except Exception as e:
                    logger.warning(f"AI 分析 {symbol} 失败: {e}")
                    # 保留技术面评分
                    scored_stocks.append(stock)

            # 按综合评分排序
            scored_stocks.sort(key=lambda x: x["score"], reverse=True)
            return scored_stocks[:top_n]

        except Exception as e:
            logger.warning(f"AI 深度分析失败: {e}")
            return candidates[:top_n]

    async def _calculate_score(
        self,
        symbol: str,
        market: Market,
        strategy: str,
    ) -> float:
        """计算股票评分（单只，兼容旧接口）"""
        try:
            indicators = await self.data_service.get_technical_indicators(symbol, market)

            score = 50.0

            # 均线评分
            if indicators.ma5 > indicators.ma10 > indicators.ma20:
                score += 10
            elif indicators.ma5 < indicators.ma10 < indicators.ma20:
                score -= 10

            # MACD 评分
            if indicators.macd > indicators.macd_signal:
                score += 10
            if indicators.macd_hist > 0:
                score += 5

            # RSI 评分
            if 30 < indicators.rsi_6 < 70:
                score += 5
            elif indicators.rsi_6 < 30:
                score += 10
            elif indicators.rsi_6 > 70:
                score -= 5

            # KDJ 评分
            if indicators.kdj_k > indicators.kdj_d:
                score += 5

            # 布林带评分
            if indicators.boll_middle > 0:
                score += 5

            return min(max(score, 0), 100)

        except Exception as e:
            logger.warning(f"计算 {symbol} 评分失败: {e}")
            return 50.0


async def get_stock_recommendations(
    market: str = "A",
    top_n: int = 10,
    strategy: str = "comprehensive",
    use_ai_screen: bool = True,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> list[dict]:
    """获取股票推荐（便捷函数）"""
    picker = StockPicker()
    market_enum = Market(market)
    return await picker.recommend(
        market_enum,
        top_n,
        strategy,
        use_ai_screen=use_ai_screen,
        progress_callback=progress_callback,
    )
