"""QUANTAXIS 数据桥接"""

import pandas as pd
from typing import Optional
from src.infra.logger import get_logger

logger = get_logger("quantaxis_data_bridge")


class QADataBridge:
    """QUANTAXIS 数据桥接器"""

    def __init__(self):
        self._qa = None

    def _ensure_import(self):
        """确保 QUANTAXIS 已导入"""
        if self._qa is None:
            try:
                import QUANTAXIS as QA
                self._qa = QA
            except ImportError:
                raise ImportError("QUANTAXIS 未安装，请运行: pip install quantaxis")

    def fetch_stock_day(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """获取日线数据"""
        self._ensure_import()
        try:
            df = self._qa.QA_fetch_stock_day(
                code=code,
                start=start_date,
                end=end_date,
            )
            return df
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
            df = self._qa.QA_fetch_stock_min(
                code=code,
                start=start_date,
                end=end_date,
                frequence=frequency,
            )
            return df
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
