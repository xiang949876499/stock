import backtrader as bt
from src.infra.logger import get_logger

logger = get_logger("backtrader_strategies")


class MACrossStrategy(bt.Strategy):
    """均线交叉策略"""

    params = (
        ('fast_period', 5),
        ('slow_period', 20),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if self.crossover > 0:
            self.buy()
        elif self.crossover < 0:
            self.sell()


class MACDStrategy(bt.Strategy):
    """MACD 策略"""

    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period,
        )

    def next(self):
        if self.macd.macd[0] > self.macd.signal[0] and self.macd.macd[-1] <= self.macd.signal[-1]:
            self.buy()
        elif self.macd.macd[0] < self.macd.signal[0] and self.macd.macd[-1] >= self.macd.signal[-1]:
            self.sell()


class RSIStrategy(bt.Strategy):
    """RSI 策略"""

    params = (
        ('period', 14),
        ('overbought', 70),
        ('oversold', 30),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(period=self.params.period)

    def next(self):
        if self.rsi[0] < self.params.oversold:
            self.buy()
        elif self.rsi[0] > self.params.overbought:
            self.sell()


class BollingerStrategy(bt.Strategy):
    """布林带策略"""

    params = (
        ('period', 20),
        ('devfactor', 2),
    )

    def __init__(self):
        self.boll = bt.indicators.BollingerBands(
            period=self.params.period,
            devfactor=self.params.devfactor,
        )

    def next(self):
        if self.data.close[0] < self.boll.lines.bot[0]:
            self.buy()
        elif self.data.close[0] > self.boll.lines.top[0]:
            self.sell()


# 策略注册表
STRATEGY_REGISTRY = {
    "ma_cross": MACrossStrategy,
    "macd": MACDStrategy,
    "rsi": RSIStrategy,
    "bollinger": BollingerStrategy,
}


def list_strategies() -> list[str]:
    """列出可用策略"""
    return list(STRATEGY_REGISTRY.keys())


def get_strategy_class(name: str):
    """获取策略类"""
    return STRATEGY_REGISTRY.get(name)
