import backtrader as bt
import pandas as pd
from typing import Optional
from src.infra.logger import get_logger

logger = get_logger("backtrader_data_feed")


class DataFrameDataFeed(bt.feeds.PandasData):
    """DataFrame 数据源适配器

    支持从 pandas DataFrame 创建 backtrader 数据源，支持列名映射。

    使用方式:
        df = pd.DataFrame({...}, index=pd.date_range(...))
        feed = DataFrameDataFeed(dataname=df)

        # 或使用工厂函数
        feed = DataFrameDataFeed.from_dataframe(df, column_mapping={'Date': 'datetime', ...})
    """

    params = (
        ('datetime', 'datetime'),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),
    )

    def __init__(self, *args, **kwargs):
        """初始化数据源"""
        super().__init__(*args, **kwargs)
        logger.info(f"创建数据源，共 {len(self.p.dataname)} 条记录")

    @classmethod
    def from_dataframe(
        cls,
        df: pd.DataFrame,
        column_mapping: Optional[dict] = None,
        **kwargs,
    ) -> "DataFrameDataFeed":
        """从 DataFrame 创建数据源

        Args:
            df: pandas DataFrame
            column_mapping: 列名映射 {'原始列名': '标准列名'}
            **kwargs: 传递给 PandasData 的其他参数

        Returns:
            DataFrameDataFeed 实例
        """
        if column_mapping:
            df = df.rename(columns=column_mapping)

        # 确保 datetime 列存在并设为索引
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')

        return cls(dataname=df, **kwargs)


def create_data_feed_from_service(
    symbol: str,
    start_date: str,
    end_date: str,
) -> Optional[DataFrameDataFeed]:
    """从 DataService 创建数据源"""
    from src.data.service import DataService

    try:
        service = DataService()
        df = service.get_stock_data(symbol, start_date, end_date)

        if df is None or df.empty:
            logger.warning(f"无法获取数据: {symbol}")
            return None

        return DataFrameDataFeed(df)
    except Exception as e:
        logger.error(f"创建数据源失败: {e}")
        return None
