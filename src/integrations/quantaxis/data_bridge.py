"""QUANTAXIS 数据桥接 - 使用 akshare 获取数据"""

import pandas as pd
from typing import Optional
from src.infra.logger import get_logger

logger = get_logger("quantaxis_data_bridge")


class QADataBridge:
    """QUANTAXIS 数据桥接器（使用 akshare）"""

    def __init__(self):
        self._ak = None

    def _ensure_import(self):
        """确保 akshare 已导入"""
        if self._ak is None:
            try:
                import akshare as ak
                self._ak = ak
                logger.info("akshare 导入成功")
            except ImportError:
                raise ImportError("akshare 未安装，请运行: pip install akshare")

    def fetch_stock_day(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """获取日线数据"""
        self._ensure_import()
        try:
            # 使用 akshare 获取日线数据
            df = self._ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust="qfq"
            )

            if df is None or df.empty:
                logger.warning(f"未获取到数据: {code}")
                return pd.DataFrame()

            # 转换列名
            df = df.rename(columns={
                '日期': 'datetime',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'amount',
            })

            # 转换日期格式
            df['datetime'] = pd.to_datetime(df['datetime'])

            return df[['datetime', 'open', 'high', 'low', 'close', 'volume', 'amount']]
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
        """获取分钟线数据"""
        self._ensure_import()
        try:
            # 分钟级别映射
            period_map = {
                '1min': '1',
                '5min': '5',
                '15min': '15',
                '30min': '30',
                '60min': '60',
            }
            period = period_map.get(frequency, '15')

            # 使用 akshare 获取分钟线数据
            df = self._ak.stock_zh_a_hist_min_em(
                symbol=code,
                period=period,
                start_date=f"{start_date} 09:30:00",
                end_date=f"{end_date} 15:00:00",
                adjust="qfq"
            )

            if df is None or df.empty:
                logger.warning(f"未获取到数据: {code}")
                return pd.DataFrame()

            # 转换列名
            df = df.rename(columns={
                '时间': 'datetime',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low',
                '收盘': 'close',
                '成交量': 'volume',
                '成交额': 'amount',
            })

            # 转换日期格式
            df['datetime'] = pd.to_datetime(df['datetime'])

            return df[['datetime', 'open', 'high', 'low', 'close', 'volume', 'amount']]
        except Exception as e:
            logger.error(f"获取分钟线数据失败: {e}")
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
