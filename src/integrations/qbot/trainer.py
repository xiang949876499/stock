"""Qbot 强化学习训练器"""

import numpy as np
import pandas as pd
from typing import Optional, Dict, Any
from dataclasses import dataclass
from pathlib import Path

from src.infra.logger import get_logger

logger = get_logger("qbot_trainer")


@dataclass
class TrainingConfig:
    """训练配置"""
    algorithm: str = "ppo"
    total_timesteps: int = 100000
    learning_rate: float = 0.0003
    batch_size: int = 64
    n_epochs: int = 10
    gamma: float = 0.99
    model_save_path: str = "./models/qbot"


@dataclass
class TrainingResult:
    """训练结果"""
    model_id: str
    algorithm: str
    total_timesteps: int
    final_reward: float
    model_path: str
    metadata: Dict[str, Any]


class StockTradingEnv:
    """股票交易环境"""

    def __init__(self, data: pd.DataFrame, initial_balance: float = 100000):
        self.data = data
        self.initial_balance = initial_balance
        self.reset()

    def reset(self):
        """重置环境"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.shares_held = 0
        self.total_profit = 0
        self.trades = []
        return self._get_observation()

    def _get_observation(self):
        """获取观察值"""
        if self.current_step >= len(self.data):
            return np.zeros(10)

        row = self.data.iloc[self.current_step]
        return np.array([
            row.get('open', 0),
            row.get('high', 0),
            row.get('low', 0),
            row.get('close', 0),
            row.get('volume', 0),
            self.balance,
            self.shares_held,
            self.total_profit,
            self.current_step / len(self.data),
            1.0 if self.shares_held > 0 else 0.0,
        ])

    def step(self, action):
        """
        执行动作
        action: 0=持有, 1=买入, 2=卖出
        """
        if self.current_step >= len(self.data) - 1:
            return self._get_observation(), 0, True, {}

        current_price = self.data.iloc[self.current_step]['close']
        next_price = self.data.iloc[self.current_step + 1]['close']

        reward = 0

        # 执行动作
        if action == 1:  # 买入
            if self.balance >= current_price * 100:
                shares_to_buy = int(self.balance / (current_price * 100)) * 100
                cost = shares_to_buy * current_price
                self.balance -= cost
                self.shares_held += shares_to_buy
                self.trades.append({
                    'step': self.current_step,
                    'action': 'buy',
                    'price': current_price,
                    'shares': shares_to_buy,
                })
                reward = -0.01  # 交易成本

        elif action == 2:  # 卖出
            if self.shares_held > 0:
                revenue = self.shares_held * current_price
                self.balance += revenue
                profit = (current_price - self.data.iloc[self.current_step - 1]['close']) * self.shares_held
                self.total_profit += profit
                self.trades.append({
                    'step': self.current_step,
                    'action': 'sell',
                    'price': current_price,
                    'shares': self.shares_held,
                })
                self.shares_held = 0
                reward = profit / self.initial_balance  # 收益率作为奖励

        # 更新步骤
        self.current_step += 1

        # 计算总资产
        total_assets = self.balance + self.shares_held * next_price
        done = self.current_step >= len(self.data) - 1

        if done:
            # 最终奖励
            final_return = (total_assets - self.initial_balance) / self.initial_balance
            reward += final_return * 10

        return self._get_observation(), reward, done, {
            'total_assets': total_assets,
            'balance': self.balance,
            'shares_held': self.shares_held,
            'total_profit': self.total_profit,
        }


class QbotTrainer:
    """Qbot 训练器"""

    def __init__(self, config: Optional[TrainingConfig] = None):
        self.config = config or TrainingConfig()
        self.model = None

    def _create_env(self, data: pd.DataFrame):
        """创建训练环境"""
        return StockTradingEnv(data)

    def _create_model(self, env):
        """创建模型"""
        try:
            from stable_baselines3 import PPO, A2C, DQN, SAC

            algorithm_map = {
                'ppo': PPO,
                'a2c': A2C,
                'dqn': DQN,
                'sac': SAC,
            }

            model_class = algorithm_map.get(self.config.algorithm.lower())
            if model_class is None:
                raise ValueError(f"不支持的算法: {self.config.algorithm}")

            model = model_class(
                'MlpPolicy',
                env,
                learning_rate=self.config.learning_rate,
                batch_size=self.config.batch_size,
                n_epochs=self.config.n_epochs,
                gamma=self.config.gamma,
                verbose=1,
            )

            return model
        except ImportError as e:
            logger.error(f"stable_baselines3 未安装: {e}")
            raise

    def train(
        self,
        data: pd.DataFrame,
        symbols: list[str],
    ) -> TrainingResult:
        """
        训练模型

        Args:
            data: 训练数据
            symbols: 股票代码列表

        Returns:
            TrainingResult: 训练结果
        """
        logger.info(f"开始训练: 算法={self.config.algorithm}, 股票={symbols}")

        # 创建环境
        env = self._create_env(data)

        # 创建模型
        self.model = self._create_model(env)

        # 训练模型
        self.model.learn(total_timesteps=self.config.total_timesteps)

        # 生成模型 ID
        model_id = f"{self.config.algorithm}_{len(symbols)}stocks_{self.config.total_timesteps}steps"

        # 保存模型
        model_path = Path(self.config.model_save_path)
        model_path.mkdir(parents=True, exist_ok=True)
        save_path = model_path / f"{model_id}.zip"
        self.model.save(str(save_path))

        logger.info(f"模型训练完成，保存到: {save_path}")

        return TrainingResult(
            model_id=model_id,
            algorithm=self.config.algorithm,
            total_timesteps=self.config.total_timesteps,
            final_reward=0.0,  # TODO: 计算最终奖励
            model_path=str(save_path),
            metadata={
                'symbols': symbols,
                'data_length': len(data),
            },
        )

    def predict(
        self,
        model_path: str,
        data: pd.DataFrame,
    ) -> Dict[str, float]:
        """
        使用模型预测

        Args:
            model_path: 模型路径
            data: 预测数据

        Returns:
            预测结果
        """
        try:
            from stable_baselines3 import PPO, A2C, DQN, SAC

            # 加载模型
            algorithm_map = {
                'ppo': PPO,
                'a2c': A2C,
                'dqn': DQN,
                'sac': SAC,
            }

            # 从路径解析算法
            algorithm = 'ppo'
            for algo_name in algorithm_map:
                if algo_name in model_path.lower():
                    algorithm = algo_name
                    break

            model_class = algorithm_map.get(algorithm)
            model = model_class.load(model_path)

            # 创建环境
            env = self._create_env(data)

            # 预测
            obs = env.reset()
            actions = []

            for _ in range(len(data)):
                action, _ = model.predict(obs, deterministic=True)
                actions.append(int(action))
                obs, _, done, _ = env.step(action)
                if done:
                    break

            return {
                'actions': actions,
                'buy_count': actions.count(1),
                'sell_count': actions.count(2),
                'hold_count': actions.count(0),
            }
        except Exception as e:
            logger.error(f"预测失败: {e}")
            raise


def train_model(
    symbols: list[str],
    start_date: str,
    end_date: str,
    algorithm: str = "ppo",
    total_timesteps: int = 100000,
) -> TrainingResult:
    """
    训练模型的便捷函数

    Args:
        symbols: 股票代码列表
        start_date: 开始日期
        end_date: 结束日期
        algorithm: 算法名称
        total_timesteps: 训练步数

    Returns:
        TrainingResult: 训练结果
    """
    import akshare as ak

    # 获取训练数据
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
            logger.error(f"获取数据失败 {symbol}: {e}")

    if not all_data:
        raise ValueError("没有获取到训练数据")

    # 合并数据
    combined_data = pd.concat(all_data, ignore_index=True)

    # 创建训练配置
    config = TrainingConfig(
        algorithm=algorithm,
        total_timesteps=total_timesteps,
    )

    # 创建训练器并训练
    trainer = QbotTrainer(config)
    result = trainer.train(combined_data, symbols)

    return result
