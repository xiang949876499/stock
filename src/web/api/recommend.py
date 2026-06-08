"""股票推荐 API"""

from fastapi import APIRouter, Query, Depends
from typing import Optional

from src.data.models import Market
from src.analysis.service import AnalysisService
from src.analysis.strategies.stock_picker import StockPicker, get_stock_recommendations
from src.web.deps import get_analysis_service, get_data_service
from src.data.service import DataService
from src.exceptions import DataProviderError, AIProviderError
from src.infra.logger import get_logger

logger = get_logger("recommend_api")

router = APIRouter(prefix="/recommend", tags=["recommend"])


@router.get("/stocks")
async def recommend_stocks(
    market: str = Query("A", pattern="^(A|HK)$"),
    top_n: int = Query(10, ge=1, le=50),
    strategy: str = Query("comprehensive"),
):
    """推荐股票"""
    try:
        recommendations = await get_stock_recommendations(market, top_n, strategy)
        return {
            "market": market,
            "strategy": strategy,
            "count": len(recommendations),
            "stocks": recommendations,
        }
    except Exception as e:
        logger.error(f"推荐股票失败: {e}")
        raise DataProviderError(f"推荐股票失败: {e}")


@router.get("/stocks/analyze")
async def recommend_and_analyze(
    market: str = Query("A", pattern="^(A|HK)$"),
    top_n: int = Query(5, ge=1, le=10),
    strategy: str = Query("comprehensive"),
    analysis_service: AnalysisService = Depends(get_analysis_service),
    data_service: DataService = Depends(get_data_service),
):
    """推荐股票并进行 AI 分析"""
    try:
        # 1. 获取推荐
        recommendations = await get_stock_recommendations(market, top_n, strategy)

        # 2. 对每只股票进行 AI 分析
        results = []
        for stock in recommendations:
            try:
                # AI 分析
                analysis = await analysis_service.analyze_stock(
                    stock["symbol"],
                    strategy,
                )

                results.append({
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "market": stock["market"],
                    "technical_score": stock["score"],
                    "ai_score": analysis.score,
                    "signal": analysis.signal,
                    "trend": analysis.trend,
                    "reason": analysis.reason,
                    "combined_score": (stock["score"] + analysis.score) / 2,
                })
            except Exception as e:
                logger.warning(f"分析 {stock['symbol']} 失败: {e}")
                results.append({
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "market": stock["market"],
                    "technical_score": stock["score"],
                    "ai_score": None,
                    "signal": None,
                    "trend": None,
                    "reason": f"分析失败: {e}",
                    "combined_score": stock["score"],
                })

        # 3. 按综合评分排序
        results.sort(key=lambda x: x["combined_score"] or 0, reverse=True)

        return {
            "market": market,
            "strategy": strategy,
            "count": len(results),
            "stocks": results,
        }

    except Exception as e:
        logger.error(f"推荐并分析股票失败: {e}")
        raise AIProviderError(f"推荐并分析股票失败: {e}")


@router.get("/stocks/{symbol}/evaluate")
async def evaluate_stock(
    symbol: str,
    market: str = Query("A", pattern="^(A|HK)$"),
    strategy: str = Query("comprehensive"),
    analysis_service: AnalysisService = Depends(get_analysis_service),
):
    """评估单只股票"""
    try:
        # AI 分析
        analysis = await analysis_service.analyze_stock(symbol, strategy)

        return {
            "symbol": symbol,
            "market": market,
            "strategy": strategy,
            "score": analysis.score,
            "signal": analysis.signal,
            "trend": analysis.trend,
            "reason": analysis.reason,
        }

    except Exception as e:
        logger.error(f"评估股票失败: {e}")
        raise AIProviderError(f"评估股票失败: {e}")
