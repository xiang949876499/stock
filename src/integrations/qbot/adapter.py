"""Qbot AI 策略适配器"""

import numpy as np
import pandas as pd
from typing import Optional
from dataclasses import dataclass
from pathlib import Path

from src.integrations.base import BaseAdapter
from src.integrations.qbot.rl_strategies import RLAlgorithm, ALGORITHM_CONFIGS
from src.integrations.qbot.trainer import QbotTrainer, TrainingConfig, TrainingResult
from src.infra.logger import get_logger

logger = get_logger("qbot_adapter")


@dataclass
class PredictionResult:
    """预测结果"""
    weights: dict[str, float]
    confidence: float
    algorithm: str
    metadata: Optional[dict] = None


class QbotAdapter(BaseAdapter):
    """Qbot AI 策略适配器"""

    def __init__(self, enabled: bool = True):
        super().__init__(name="qbot", enabled=enabled)
        self.models = {}
        self.trainer = None

    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            import torch
            import stable_baselines3
            self.logger.info("Qbot 依赖初始化成功")
            return True
        except ImportError as e:
            self.logger.warning(f"Qbot 依赖未安装: {e}")
            return False

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            import torch
            return True
        except ImportError:
            return False

    def list_algorithms(self) -> list[str]:
        """列出可用算法"""
        return [a.value for a in RLAlgorithm]

    async def train(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        algorithm: str = "ppo",
        total_timesteps: int = 100000,
    ) -> TrainingResult:
        """
        训练模型

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            algorithm: 算法名称 (ppo/a2c/dqn/sac)
            total_timesteps: 训练步数

        Returns:
            TrainingResult: 训练结果
        """
        self.logger.info(f"开始训练: 算法={algorithm}, 股票={symbols}")

        # 创建训练配置
        config = TrainingConfig(
            algorithm=algorithm,
            total_timesteps=total_timesteps,
        )

        # 创建训练器
        self.trainer = QbotTrainer(config)

        # 获取训练数据
        import akshare as ak
        all_data = []
        for symbol in symbols:
            try:
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust="qfq"
                )
                if df is not None and not df.empty:
                    df = df.rename(columns={
                        '日期': 'datetime',
                        '开盘': 'open',
                        '最高': 'high',
                        '最低': 'low',
                        '收盘': 'close',
                        '成交量': 'volume',
                    })
                    all_data.append(df)
            except Exception as e:
                self.logger.error(f"获取数据失败 {symbol}: {e}")

        if not all_data:
            raise ValueError("没有获取到训练数据")

        # 合并数据
        combined_data = pd.concat(all_data, ignore_index=True)

        # 训练模型
        result = self.trainer.train(combined_data, symbols)

        # 保存模型到内存
        self.models[result.model_id] = {
            'path': result.model_path,
            'algorithm': algorithm,
            'symbols': symbols,
        }

        return result

    async def predict(
        self,
        symbols: list[str],
        algorithm: str = "ppo",
        model_id: Optional[str] = None,
    ) -> PredictionResult:
        """
        预测信号

        Args:
            symbols: 股票代码列表
            algorithm: 算法名称
            model_id: 模型 ID
        """
        self.logger.info(f"开始预测: {symbols}, 算法: {algorithm}")

        # 如果没有指定模型，使用最新的模型
        if model_id is None:
            if not self.models:
                # 返回等权重
                weights = {symbol: 1.0 / len(symbols) for symbol in symbols}
                return PredictionResult(
                    weights=weights,
                    confidence=0.5,
                    algorithm=algorithm,
                    metadata={"note": "使用默认等权重，未找到训练好的模型"},
                )
            model_id = list(self.models.keys())[-1]

        # 获取模型信息
        model_info = self.models.get(model_id)
        if model_info is None:
            raise ValueError(f"未找到模型: {model_id}")

        # 获取预测数据
        import akshare as ak
        all_data = []
        for symbol in symbols:
            try:
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date="20240101",
                    end_date="20241231",
                    adjust="qfq"
                )
                if df is not None and not df.empty:
                    df = df.rename(columns={
                        '日期': 'datetime',
                        '开盘': 'open',
                        '最高': 'high',
                        '最低': 'low',
                        '收盘': 'close',
                        '成交量': 'volume',
                    })
                    all_data.append(df)
            except Exception as e:
                self.logger.error(f"获取数据失败 {symbol}: {e}")

        if not all_data:
            raise ValueError("没有获取到预测数据")

        # 使用模型预测
        combined_data = pd.concat(all_data, ignore_index=True)
        predictions = self.trainer.predict(model_info['path'], combined_data)

        # 计算权重
        buy_count = predictions.get('buy_count', 0)
        sell_count = predictions.get('sell_count', 0)
        total_actions = len(predictions.get('actions', []))

        if total_actions > 0:
            buy_ratio = buy_count / total_actions
            sell_ratio = sell_count / total_actions
        else:
            buy_ratio = 0.5
            sell_ratio = 0.5

        # 生成权重
        weights = {}
        for symbol in symbols:
            # 简化处理：根据买入比例分配权重
            weights[symbol] = buy_ratio / len(symbols)

        return PredictionResult(
            weights=weights,
            confidence=0.7,
            algorithm=algorithm,
            metadata={
                "model_id": model_id,
                "predictions": predictions,
            },
        )
