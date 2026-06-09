"""ML 策略封装"""

from enum import Enum


class MLStrategy(str, Enum):
    """ML 策略"""
    XGBOOST = "xgboost"
    RANDOM_FOREST = "random_forest"
    LIGHTGBM = "lightgbm"
    LINEAR_REGRESSION = "linear_regression"


STRATEGY_CONFIGS = {
    MLStrategy.XGBOOST: {
        "name": "XGBoost",
        "description": "梯度提升树",
        "library": "xgboost",
    },
    MLStrategy.RANDOM_FOREST: {
        "name": "Random Forest",
        "description": "随机森林",
        "library": "sklearn",
    },
    MLStrategy.LIGHTGBM: {
        "name": "LightGBM",
        "description": "轻量梯度提升",
        "library": "lightgbm",
    },
    MLStrategy.LINEAR_REGRESSION: {
        "name": "Linear Regression",
        "description": "线性回归",
        "library": "sklearn",
    },
}
