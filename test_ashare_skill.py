"""测试 a-share-skill 集成"""

import os
# 禁用代理
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

import asyncio
from src.data.providers.ashare_skill_provider import AShareSkillProvider
from src.data.models import Market
from datetime import date


async def test_fetch_daily():
    """测试获取日线数据"""
    print("=" * 60)
    print("测试 a-share-skill 日线数据获取")
    print("=" * 60)

    provider = AShareSkillProvider()

    try:
        df = await provider.fetch_daily(
            symbol="600519",
            market=Market.A,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 31)
        )

        if df is not None and not df.empty:
            print(f"\n获取成功: {len(df)} 条记录")
            print(f"\n数据预览:")
            print(df.head())
            print(f"\n列名: {df.columns.tolist()}")
        else:
            print("\n获取失败: 无数据")

    except Exception as e:
        print(f"\n获取失败: {e}")


async def test_fetch_realtime():
    """测试获取实时行情"""
    print("\n" + "=" * 60)
    print("测试 a-share-skill 实时行情获取")
    print("=" * 60)

    provider = AShareSkillProvider()

    try:
        results = await provider.fetch_realtime(["600519", "000858"])

        if results:
            print(f"\n获取成功: {len(results)} 条记录")
            for data in results:
                print(f"\n{data}")
        else:
            print("\n获取失败: 无数据")

    except Exception as e:
        print(f"\n获取失败: {e}")


async def test_strategies():
    """测试策略"""
    print("\n" + "=" * 60)
    print("测试 a-share-skill 策略")
    print("=" * 60)

    from src.analysis.strategies.base import STRATEGIES

    print(f"\n可用策略: {len(STRATEGIES)} 个")
    for name in STRATEGIES.keys():
        print(f"  - {name}")


async def main():
    """主函数"""
    print("Stock Hub - a-share-skill 集成测试")
    print("=" * 60)

    # 测试策略
    await test_strategies()

    # 测试数据获取（可能需要网络）
    # await test_fetch_daily()
    # await test_fetch_realtime()


if __name__ == "__main__":
    asyncio.run(main())
