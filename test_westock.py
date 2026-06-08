"""测试 westock-data-skillhub 集成"""

import os
# 禁用代理
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

import asyncio
from src.data.providers.westock_provider import WestockProvider
from src.data.models import Market


async def test_search():
    """测试搜索功能"""
    print("=" * 60)
    print("测试 westock-data-skillhub 搜索")
    print("=" * 60)

    provider = WestockProvider()

    try:
        results = await provider.search("贵州茅台")
        print(f"\n搜索结果: {len(results)} 条")
        for r in results:
            print(f"  {r}")
    except Exception as e:
        print(f"\n搜索失败: {e}")


async def test_kline():
    """测试 K 线数据"""
    print("\n" + "=" * 60)
    print("测试 westock-data-skillhub K线数据")
    print("=" * 60)

    provider = WestockProvider()

    try:
        from datetime import date, timedelta
        df = await provider.fetch_daily(
            symbol="600519",
            market=Market.A,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today()
        )

        if df is not None and not df.empty:
            print(f"\n获取成功: {len(df)} 条记录")
            print(f"\n数据预览:")
            print(df.head())
        else:
            print("\n获取失败: 无数据")

    except Exception as e:
        print(f"\n获取失败: {e}")


async def test_technical():
    """测试技术指标"""
    print("\n" + "=" * 60)
    print("测试 westock-data-skillhub 技术指标")
    print("=" * 60)

    provider = WestockProvider()

    try:
        result = await provider.fetch_technical(
            symbol="600519",
            market=Market.A
        )

        print(f"\n技术指标:")
        print(result)

    except Exception as e:
        print(f"\n获取失败: {e}")


async def test_hot():
    """测试热搜"""
    print("\n" + "=" * 60)
    print("测试 westock-data-skillhub 热搜")
    print("=" * 60)

    provider = WestockProvider()

    try:
        results = await provider.fetch_hot(limit=5)
        print(f"\n热搜: {len(results)} 条")
        for r in results:
            print(f"  {r}")
    except Exception as e:
        print(f"\n获取失败: {e}")


async def main():
    """主函数"""
    print("Stock Hub - westock-data-skillhub 集成测试")
    print("=" * 60)

    # 测试搜索
    await test_search()

    # 测试热搜
    await test_hot()

    # 测试 K 线（需要网络）
    # await test_kline()

    # 测试技术指标（需要网络）
    # await test_technical()


if __name__ == "__main__":
    asyncio.run(main())
