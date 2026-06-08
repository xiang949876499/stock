"""预下载股票数据"""

import os
# 禁用代理
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

import asyncio
from datetime import date, timedelta
from src.data.providers.akshare_provider import AkShareProvider
from src.data.storage.parquet import ParquetStorage
from src.data.models import Market
from src.infra.logger import setup_logger

logger = setup_logger("download")


async def download_stock(symbol: str, market: Market):
    """下载单只股票数据"""
    provider = AkShareProvider()
    storage = ParquetStorage()

    try:
        # 检查是否已存在
        if storage.exists(symbol, market):
            logger.info(f"数据已存在: {symbol}")
            return True

        # 下载数据
        start_date = date(2024, 1, 1)
        end_date = date.today()

        logger.info(f"正在下载: {symbol} ({start_date} ~ {end_date})")
        df = await provider.fetch_daily(symbol, market, start_date, end_date)

        if df is not None and not df.empty:
            storage.save_daily(df, symbol, market)
            logger.info(f"下载成功: {symbol}, {len(df)} 条记录")
            return True
        else:
            logger.warning(f"下载失败: {symbol}, 无数据")
            return False

    except Exception as e:
        logger.error(f"下载失败: {symbol}, {e}")
        return False


async def main():
    """主函数"""
    # A 股股票列表
    a_stocks = [
        "600519", "000858", "601318", "000333", "600036",
        "000651", "601012", "300750", "600900", "601398",
    ]

    # 港股股票列表
    hk_stocks = ["00700", "09988", "03690"]

    print("=" * 60)
    print("Stock Hub 数据预下载")
    print("=" * 60)

    # 下载 A 股
    print("\n正在下载 A 股数据...")
    a_success = 0
    for symbol in a_stocks:
        success = await download_stock(symbol, Market.A)
        if success:
            a_success += 1
        await asyncio.sleep(1)  # 避免请求过快

    # 下载港股
    print("\n正在下载港股数据...")
    hk_success = 0
    for symbol in hk_stocks:
        success = await download_stock(symbol, Market.HK)
        if success:
            hk_success += 1
        await asyncio.sleep(1)

    print("\n" + "=" * 60)
    print(f"下载完成: A股 {a_success}/{len(a_stocks)}, 港股 {hk_success}/{len(hk_stocks)}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
