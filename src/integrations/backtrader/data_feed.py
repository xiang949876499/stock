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
    """从 akshare 创建数据源"""
    try:
        import akshare as ak

        # 获取日线数据
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date.replace('-', ''),
            end_date=end_date.replace('-', ''),
            adjust="qfq"
        )

        if df is None or df.empty:
            logger.warning(f"无法获取数据: {symbol}")
            return None

        # 转换列名
        df = df.rename(columns={
            '日期': 'datetime',
            '开盘': 'open',
            '最高': 'high',
            '最低': 'low',
            '收盘': 'close',
            '成交量': 'volume',
        })

        # 转换日期格式
        df['datetime'] = pd.to_datetime(df['datetime'])

        # 只保留需要的列
        df = df[['datetime', 'open', 'high', 'low', 'close', 'volume']]

        return DataFrameDataFeed.from_dataframe(df)
    except Exception as e:
        logger.error(f"创建数据源失败: {e}")
        return None
