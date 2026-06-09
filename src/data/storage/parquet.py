"""Parquet 存储"""

from pathlib import Path
from typing import Optional
import pandas as pd

from src.data.models import Market
from src.infra.logger import get_logger

logger = get_logger("parquet")


class ParquetStorage:
    """Parquet 存储"""

    def __init__(self, data_dir: str = "./data"):
        """初始化存储"""
        self.data_dir = Path(data_dir)
        self.daily_dir = self.data_dir / "daily"
        self.daily_dir.mkdir(parents=True, exist_ok=True)

    def save_daily(
        self,
        df: pd.DataFrame,
        symbol: str,
        market: Market
    ):
        """保存日线数据"""
        market_dir = self.daily_dir / market.value
        market_dir.mkdir(parents=True, exist_ok=True)

        file_path = market_dir / f"{symbol}.parquet"
        df.to_parquet(file_path, index=False)
        logger.info(f"保存日线数据: {file_path}")

    def load_daily(
        self,
        symbol: str,
        market: Market,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """加载日线数据"""
        file_path = self.daily_dir / market.value / f"{symbol}.parquet"

        if not file_path.exists():
            logger.warning(f"日线数据文件不存在: {file_path}")
            return None

        df = pd.read_parquet(file_path)

        # 过滤日期
        if start_date:
            df = df[df["date"] >= start_date]
        if end_date:
            df = df[df["date"] <= end_date]

        return df

    def get_last_date(
        self,
        symbol: str,
        market: Market
    ) -> Optional[str]:
        """获取最后更新日期"""
        df = self.load_daily(symbol, market)
        if df is None or df.empty:
            return None
        return df["date"].max()

    def exists(
        self,
        symbol: str,
        market: Market
    ) -> bool:
        """检查数据是否存在"""
        file_path = self.daily_dir / market.value / f"{symbol}.parquet"
        return file_path.exists()

    def delete(
        self,
        symbol: str,
        market: Market
    ):
        """删除数据"""
        file_path = self.daily_dir / market.value / f"{symbol}.parquet"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"删除日线数据: {file_path}")
