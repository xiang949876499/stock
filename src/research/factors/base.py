"""因子基类"""

from abc import ABC, abstractmethod
from typing import Callable, Any
from dataclasses import dataclass
import pandas as pd


@dataclass
class Factor:
    """因子"""
    name: str
    func: Callable
    description: str = ""
    category: str = "custom"


class FactorRegistry:
    """因子注册中心"""

    def __init__(self):
        self.factors: dict[str, Factor] = {}

    def register(
        self,
        name: str,
        func: Callable,
        description: str = "",
        category: str = "custom"
    ):
        """注册因子"""
        self.factors[name] = Factor(
            name=name,
            func=func,
            description=description,
            category=category
        )

    def calculate(
        self,
        name: str,
        df: pd.DataFrame
    ) -> pd.Series:
        """计算因子"""
        if name not in self.factors:
            raise ValueError(f"因子 {name} 未注册")
        return self.factors[name].func(df)

    def get_factor(self, name: str) -> Factor:
        """获取因子"""
        if name not in self.factors:
            raise ValueError(f"因子 {name} 未注册")
        return self.factors[name]

    def list_factors(self) -> list[str]:
        """列出所有因子"""
        return list(self.factors.keys())

    def list_by_category(self, category: str) -> list[str]:
        """按类别列出因子"""
        return [
            name for name, factor in self.factors.items()
            if factor.category == category
        ]


# 内置因子函数
class BuiltinFactors:
    """内置因子库"""

    @staticmethod
    def ma5(df: pd.DataFrame) -> pd.Series:
        """5日均线"""
        return df["close"].rolling(window=5).mean()

    @staticmethod
    def ma10(df: pd.DataFrame) -> pd.Series:
        """10日均线"""
        return df["close"].rolling(window=10).mean()

    @staticmethod
    def ma20(df: pd.DataFrame) -> pd.Series:
        """20日均线"""
        return df["close"].rolling(window=20).mean()

    @staticmethod
    def ma60(df: pd.DataFrame) -> pd.Series:
        """60日均线"""
        return df["close"].rolling(window=60).mean()

    @staticmethod
    def volume_ratio(df: pd.DataFrame) -> pd.Series:
        """量比"""
        return df["volume"] / df["volume"].rolling(window=5).mean()

    @staticmethod
    def price_change(df: pd.DataFrame) -> pd.Series:
        """涨跌幅"""
        return df["close"].pct_change()

    @staticmethod
    def volatility(df: pd.DataFrame) -> pd.Series:
        """波动率"""
        return df["close"].pct_change().rolling(window=20).std()


def create_default_registry() -> FactorRegistry:
    """创建默认因子注册表"""
    registry = FactorRegistry()

    # 注册内置因子
    builtin = BuiltinFactors()

    registry.register("ma5", builtin.ma5, "5日均线", "ma")
    registry.register("ma10", builtin.ma10, "10日均线", "ma")
    registry.register("ma20", builtin.ma20, "20日均线", "ma")
    registry.register("ma60", builtin.ma60, "60日均线", "ma")
    registry.register("volume_ratio", builtin.volume_ratio, "量比", "volume")
    registry.register("price_change", builtin.price_change, "涨跌幅", "price")
    registry.register("volatility", builtin.volatility, "波动率", "risk")

    return registry
