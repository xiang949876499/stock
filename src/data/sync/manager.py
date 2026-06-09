"""数据同步管理器"""

from datetime import date, timedelta
from typing import Optional
import pandas as pd

from src.data.models import Market
from src.data.providers.base import DataProvider
from src.data.storage.parquet import ParquetStorage
from src.infra.logger import get_logger

logger = get_logger("sync")


class DataSyncManager:
    """数据同步管理器"""

    def __init__(
        self,
        provider: DataProvider,
        storage: ParquetStorage
    ):
        """初始化同步管理器"""
        self.provider = provider
        self.storage = storage

    async def sync_daily(
        self,
        symbol: str,
        market: Market,
        incremental: bool = True
    ):
        """同步日线数据"""
        try:
            if incremental:
                # 增量同步：只获取最新数据
                last_date = self.storage.get_last_date(symbol, market)
                if last_date:
                    start_date = pd.Timestamp(last_date).date() + timedelta(days=1)
                else:
                    start_date = date(2010, 1, 1)
            else:
                # 全量同步：获取所有历史数据
                start_date = date(2010, 1, 1)

            end_date = date.today()

            # 检查是否需要同步
            if start_date > end_date:
                logger.info(f"数据已是最新: {symbol}, {market}")
                return

            # 获取数据
            df = await self.provider.fetch_daily(
                symbol, market, start_date, end_date
            )

            if df is None or df.empty:
                logger.warning(f"未获取到数据: {symbol}, {market}")
                return

            # 数据清洗
            df = self._clean_data(df)

            # 保存数据
            if incremental and self.storage.exists(symbol, market):
                # 合并数据
                existing_df = self.storage.load_daily(symbol, market)
                if existing_df is not None:
                    df = pd.concat([existing_df, df], ignore_index=True)
                    df = df.drop_duplicates(subset=["date"], keep="last")
                    df = df.sort_values("date")

            self.storage.save_daily(df, symbol, market)
            logger.info(f"同步完成: {symbol}, {market}, {len(df)} 条记录")

        except Exception as e:
            logger.error(f"同步失败: {symbol}, {market}, {e}")
            raise

    async def sync_batch(
        self,
        symbols: list[str],
        market: Market,
        incremental: bool = True
    ):
        """批量同步日线数据"""
        success_count = 0
        fail_count = 0

        for symbol in symbols:
            try:
                await self.sync_daily(symbol, market, incremental)
                success_count += 1
            except Exception as e:
                logger.error(f"批量同步失败: {symbol}, {e}")
                fail_count += 1

        logger.info(f"批量同步完成: 成功 {success_count}, 失败 {fail_count}")

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗数据"""
        # 删除重复行
        df = df.drop_duplicates()

        # 删除空值
        if 'close' in df.columns:
            df = df.dropna(subset=["close"])

        # 确保日期格式
        if 'date' in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date

        # 按日期排序
        if 'date' in df.columns:
            df = df.sort_values("date")

        # 重置索引
        df = df.reset_index(drop=True)

        return df
