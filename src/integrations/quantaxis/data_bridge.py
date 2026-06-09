"""QUANTAXIS 数据桥接 - 使用 stock-hub DataService"""

import asyncio
import pandas as pd
from typing import Optional
from src.infra.logger import get_logger

logger = get_logger("quantaxis_data_bridge")


class QADataBridge:
    """QUANTAXIS 数据桥接器（使用 stock-hub DataService）"""

    def __init__(self):
        self._data_service = None

    def _ensure_service(self):
        """确保 DataService 已初始化"""
        if self._data_service is None:
            try:
                from src.data.service import DataService
                self._data_service = DataService()
                logger.info("DataService 初始化成功")
            except Exception as e:
                logger.error(f"DataService 初始化失败: {e}")
                raise

    def _run_async(self, coro):
        """运行异步协程"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环已在运行，使用 nest_asyncio
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(coro)
            else:
                return loop.run_until_complete(coro)
        except RuntimeError:
            # 没有事件循环，创建新的
            return asyncio.run(coro)

    def fetch_stock_day(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """获取日线数据"""
        self._ensure_service()
        try:
            from datetime import date
            from src.data.models import Market

            # 转换日期格式
            start = date.fromisoformat(start_date) if start_date else None
            end = date.fromisoformat(end_date) if end_date else None

            # 使用 DataService 获取数据（异步方法）
            df = self._run_async(self._data_service.get_daily(code, Market.A, start, end))

            if df is None or df.empty:
                logger.warning(f"未获取到数据: {code}")
                return pd.DataFrame()

            # 确保列名正确
            if 'date' in df.columns and 'datetime' not in df.columns:
                df = df.rename(columns={'date': 'datetime'})

            df['datetime'] = pd.to_datetime(df['datetime'])

            return df[['datetime', 'open', 'high', 'low', 'close', 'volume']]
        except Exception as e:
            logger.error(f"获取日线数据失败: {e}")
            return pd.DataFrame()

    def fetch_stock_min(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "15min",
    ) -> pd.DataFrame:
        """获取分钟线数据（暂不支持）"""
        logger.warning("分钟线数据暂不支持，返回空 DataFrame")
        return pd.DataFrame()

    def convert_to_standard_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """转换为标准格式"""
        if df.empty:
            return df

        # 列名映射
        column_mapping = {
            'date': 'datetime',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'amount': 'amount',
        }

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 确保 datetime 列
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])

        return df
