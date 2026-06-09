"""强化学习策略封装"""

from enum import Enum
from typing import Optional


class RLAlgorithm(str, Enum):
    """RL 算法"""
    DQN = "dqn"
    PPO = "ppo"
    A2C = "a2c"
    SAC = "sac"


ALGORITHM_CONFIGS = {
    RLAlgorithm.DQN: {
        "name": "DQN",
        "description": "Deep Q-Network",
        "library": "stable_baselines3",
    },
    RLAlgorithm.PPO: {
        "name": "PPO",
        "description": "Proximal Policy Optimization",
        "library": "stable_baselines3",
    },
    RLAlgorithm.A2C: {
        "name": "A2C",
        "description": "Advantage Actor-Critic",
        "library": "stable_baselines3",
    },
    RLAlgorithm.SAC: {
        "name": "SAC",
        "description": "Soft Actor-Critic",
        "library": "stable_baselines3",
    },
}
