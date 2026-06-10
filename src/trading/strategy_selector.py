"""动态策略选择器 — 根据市场状态选择分析策略"""

import math
from typing import ClassVar


class StrategySelector:
    """根据市场状态动态选择分析策略"""

    STRATEGIES: ClassVar[dict[str, str]] = {
        "trending": "trend",           # 趋势行情 → 趋势策略
        "volatile": "macd",            # 震荡行情 → MACD
        "oversold": "ma_cross",        # 超卖反弹 → 均线金叉
        "default": "comprehensive",    # 默认 → 综合分析
    }

    # ── 内部方法 ────────────────────────────────────────────────────

    def _get_market_state(self, closes: list[float]) -> str:
        """判断市场状态

        判断规则 (基于最近 20 个交易日):
        - 数据不足 20 条 → "default"
        - 20 日涨幅 > 5%  → "trending"
        - 20 日跌幅 > 5%  → "oversold"
        - 20 日收益率标准差 > 0.02 → "volatile"
        - 否则            → "default"
        """
        if len(closes) < 20:
            return "default"

        # 取最近 20 个收盘价
        window = closes[-20:]

        # 涨跌幅 = (最新 - 最早) / 最早
        first = window[0]
        if first == 0:
            return "default"

        change_pct = (window[-1] - first) / first

        if change_pct > 0.05:
            return "trending"
        if change_pct < -0.05:
            return "oversold"

        # 计算日收益率标准差
        returns = [
            (window[i] - window[i - 1]) / window[i - 1]
            for i in range(1, len(window))
            if window[i - 1] != 0
        ]

        if len(returns) < 2:
            return "default"

        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        std = math.sqrt(variance)

        if std > 0.02:
            return "volatile"

        return "default"

    # ── 公开接口 ────────────────────────────────────────────────────

    def select(self, closes: list[float]) -> str:
        """根据收盘价序列选择策略名称

        Args:
            closes: 历史收盘价列表 (至少最近 20 条)

        Returns:
            策略名称 (trend / macd / ma_cross / comprehensive)
        """
        state = self._get_market_state(closes)
        return self.STRATEGIES[state]
