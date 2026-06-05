"""研究服务"""

from typing import Optional
import pandas as pd

from src.research.factors.base import FactorRegistry, create_default_registry
from src.research.signals.generator import SignalGenerator, Signal, SignalStatus, SignalSource
from src.data.models import Market
from src.infra.logger import get_logger

logger = get_logger("research_service")


class ResearchService:
    """研究服务"""

    def __init__(
        self,
        factor_registry: Optional[FactorRegistry] = None,
    ):
        self.factor_registry = factor_registry or create_default_registry()
        self.signal_generator = SignalGenerator()

    def calculate_factor(self, name: str, df: pd.DataFrame) -> pd.Series:
        """计算因子"""
        return self.factor_registry.calculate(name, df)

    def calculate_factors(self, df: pd.DataFrame, factors: list[str] = None) -> pd.DataFrame:
        """计算多个因子"""
        if factors is None:
            factors = self.factor_registry.list_factors()

        result_df = df.copy()
        for factor_name in factors:
            try:
                result_df[factor_name] = self.calculate_factor(factor_name, df)
            except Exception as e:
                logger.error(f"计算因子失败: {factor_name}, {e}")

        return result_df

    def list_factors(self) -> list[str]:
        """列出因子"""
        return self.factor_registry.list_factors()

    def list_factors_by_category(self, category: str) -> list[str]:
        """按类别列出因子"""
        return self.factor_registry.list_by_category(category)

    def create_signal(
        self,
        targets: dict[str, float],
        source: str = "manual",
        universe: Optional[str] = None,
        cash_weight: float = 0.0,
        risk_overlay: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> Signal:
        """创建信号"""
        # 转换 source
        source_map = {
            "qlib": SignalSource.QLIB,
            "vnpy_alpha": SignalSource.VNPY_ALPHA,
            "manual": SignalSource.MANUAL,
            "llm_proposed": SignalSource.LLM_PROPOSED,
            "finrl_x": SignalSource.FINRL_X,
        }
        signal_source = source_map.get(source, SignalSource.MANUAL)

        return self.signal_generator.create_signal(
            targets=targets,
            source=signal_source,
            universe=universe,
            cash_weight=cash_weight,
            risk_overlay=risk_overlay,
            metadata=metadata,
        )

    def validate_signal(self, signal: Signal) -> tuple[bool, list[str]]:
        """验证信号"""
        return self.signal_generator.validate_signal(signal)

    def approve_signal(self, signal: Signal) -> Signal:
        """审批信号"""
        return self.signal_generator.approve_signal(signal)

    def publish_signal(self, signal: Signal) -> Signal:
        """发布信号"""
        return self.signal_generator.publish_signal(signal)

    def reject_signal(self, signal: Signal, reason: str = "") -> Signal:
        """拒绝信号"""
        return self.signal_generator.reject_signal(signal, reason)

    def create_signal_from_weights(
        self,
        weights: dict[str, float],
        source: str = "manual",
        normalize: bool = True,
    ) -> Signal:
        """从权重创建信号"""
        # 归一化权重
        if normalize:
            total = sum(weights.values())
            if total > 0:
                weights = {k: v / total for k, v in weights.items()}

        return self.create_signal(
            targets=weights,
            source=source,
        )

    def create_top_k_signal(
        self,
        scores: dict[str, float],
        k: int = 10,
        source: str = "manual",
    ) -> Signal:
        """创建 Top-K 信号"""
        # 按分数排序
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # 取 Top-K
        top_k = sorted_scores[:k]

        # 等权分配
        weight = 1.0 / len(top_k) if top_k else 0
        targets = {symbol: weight for symbol, _ in top_k}

        return self.create_signal(
            targets=targets,
            source=source,
        )
