"""测试推荐功能（禁用代理）"""

import os
# 禁用代理
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

import asyncio
from src.analysis.strategies.stock_picker import get_stock_recommendations
from src.analysis.service import AnalysisService
from src.analysis.ai.factory import AIModelFactory
from src.config import get_settings


async def test_recommend():
    """测试推荐功能"""
    print("正在推荐 A 股 Top 5...\n")

    # 获取推荐
    results = await get_stock_recommendations('A', 5)

    if not results:
        print("没有找到推荐股票")
        return

    print(f"找到 {len(results)} 只推荐股票:\n")
    for i, stock in enumerate(results, 1):
        print(f"{i}. {stock['symbol']} - {stock['name']} | 技术评分: {stock['score']:.1f}")

    return results


async def test_recommend_with_ai():
    """测试带 AI 分析的推荐"""
    print("\n正在推荐并进行 AI 分析...\n")

    # 获取推荐
    results = await get_stock_recommendations('A', 3)

    if not results:
        print("没有找到推荐股票")
        return

    # AI 分析
    config = get_settings()
    ai_adapter = AIModelFactory.create(config)

    if not ai_adapter:
        print("AI 未配置")
        return

    service = AnalysisService(ai_adapter)

    print(f"{'序号':<4} {'代码':<10} {'名称':<10} {'技术分':<8} {'AI分':<8} {'信号':<8} {'趋势':<8}")
    print("-" * 60)

    for i, stock in enumerate(results, 1):
        try:
            analysis = await service.analyze_stock(stock["symbol"], "comprehensive")
            print(
                f"{i:<4} {stock['symbol']:<10} {stock['name']:<10} "
                f"{stock['score']:<8.1f} {analysis.score:<8.1f} "
                f"{analysis.signal:<8} {analysis.trend:<8}"
            )
        except Exception as e:
            print(f"{i:<4} {stock['symbol']:<10} {stock['name']:<10} 分析失败: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Stock Hub 股票推荐测试")
    print("=" * 60)

    # 测试基础推荐
    asyncio.run(test_recommend())

    # 测试带 AI 分析的推荐
    # asyncio.run(test_recommend_with_ai())
