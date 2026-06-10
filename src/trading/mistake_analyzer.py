"""失误分析器 — 分析每日交易中的失误"""


class MistakeAnalyzer:
    """分析每日交易中的失误"""

    CHASE_THRESHOLD = 0.02   # 追涨杀跌阈值 2%
    STOP_LOSS_THRESHOLD = 0.03  # 止损阈值 3%
    FREQUENT_TRADE_LIMIT = 2   # 频繁交易次数上限

    def analyze(self, trades: list[dict], prices: dict[str, list[float]]) -> list[dict]:
        """分析交易失误，返回失误列表

        Args:
            trades: 交易记录列表，每条包含 symbol, side, price, created_at
            prices: 各标的的价格序列 {symbol: [price, ...]}

        Returns:
            失误列表，每条包含 type, symbol, description, severity
        """
        mistakes: list[dict] = []
        mistakes.extend(self._check_chase_high_sell_low(trades, prices))
        mistakes.extend(self._check_frequent_trading(trades))
        mistakes.extend(self._check_late_stop_loss(trades))
        return mistakes

    # ── 追涨杀跌 ────────────────────────────────────────────────────

    def _check_chase_high_sell_low(
        self, trades: list[dict], prices: dict[str, list[float]],
    ) -> list[dict]:
        """检测追涨杀跌

        - 买入后价格下跌超过阈值 → 追涨
        - 卖出后价格上涨超过阈值 → 杀跌
        """
        mistakes: list[dict] = []

        for trade in trades:
            symbol = trade["symbol"]
            side = trade["side"]
            trade_price = trade["price"]
            price_series = prices.get(symbol, [])
            if not price_series or trade_price == 0:
                continue

            if side == "BUY":
                # 取买入后的价格序列（不含买入时的价格）
                after_prices = self._prices_after(trade_price, price_series)
                if after_prices:
                    min_after = min(after_prices)
                    drop_pct = (trade_price - min_after) / trade_price
                    if drop_pct > self.CHASE_THRESHOLD:
                        mistakes.append({
                            "type": "追涨杀跌",
                            "symbol": symbol,
                            "description": (
                                f"买入价 {trade_price}，之后最低跌至 {min_after}，"
                                f"跌幅 {drop_pct:.1%}，疑似追涨"
                            ),
                            "severity": "high" if drop_pct > 0.05 else "medium",
                        })

            elif side == "SELL":
                after_prices = self._prices_after(trade_price, price_series)
                if after_prices:
                    max_after = max(after_prices)
                    rise_pct = (max_after - trade_price) / trade_price
                    if rise_pct > self.CHASE_THRESHOLD:
                        mistakes.append({
                            "type": "追涨杀跌",
                            "symbol": symbol,
                            "description": (
                                f"卖出价 {trade_price}，之后最高涨至 {max_after}，"
                                f"涨幅 {rise_pct:.1%}，疑似杀跌"
                            ),
                            "severity": "high" if rise_pct > 0.05 else "medium",
                        })

        return mistakes

    # ── 频繁交易 ────────────────────────────────────────────────────

    def _check_frequent_trading(self, trades: list[dict]) -> list[dict]:
        """检测频繁交易：同标的当天交易超过上限"""
        mistakes: list[dict] = []
        symbol_counts: dict[str, int] = {}

        for trade in trades:
            symbol = trade["symbol"]
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

        for symbol, count in symbol_counts.items():
            if count > self.FREQUENT_TRADE_LIMIT:
                mistakes.append({
                    "type": "频繁交易",
                    "symbol": symbol,
                    "description": f"当天交易 {count} 次，超过 {self.FREQUENT_TRADE_LIMIT} 次上限",
                    "severity": "medium",
                })

        return mistakes

    # ── 止损不及时 ──────────────────────────────────────────────────

    def _check_late_stop_loss(self, trades: list[dict]) -> list[dict]:
        """检测止损不及时：找到买入-卖出配对，亏损超过阈值"""
        mistakes: list[dict] = []

        # 按标的分组，保持时间顺序
        by_symbol: dict[str, list[dict]] = {}
        for trade in trades:
            symbol = trade["symbol"]
            by_symbol.setdefault(symbol, []).append(trade)

        for symbol, symbol_trades in by_symbol.items():
            buy_price: float | None = None
            for trade in symbol_trades:
                if trade["side"] == "BUY":
                    buy_price = trade["price"]
                elif trade["side"] == "SELL" and buy_price is not None:
                    loss_pct = (buy_price - trade["price"]) / buy_price
                    if loss_pct > self.STOP_LOSS_THRESHOLD:
                        mistakes.append({
                            "type": "止损不及时",
                            "symbol": symbol,
                            "description": (
                                f"买入价 {buy_price}，卖出价 {trade['price']}，"
                                f"亏损 {loss_pct:.1%}，超过 {self.STOP_LOSS_THRESHOLD:.0%} 止损线"
                            ),
                            "severity": "high",
                        })
                    buy_price = None

        return mistakes

    # ── 辅助方法 ────────────────────────────────────────────────────

    @staticmethod
    def _prices_after(trade_price: float, price_series: list[float]) -> list[float]:
        """返回价格序列中与交易价不同的后续价格

        简化处理：跳过第一个等于 trade_price 的元素作为交易时刻，
        之后的所有价格视为交易后价格。
        """
        found_trade = False
        after: list[float] = []
        for p in price_series:
            if not found_trade and p == trade_price:
                found_trade = True
                continue
            if found_trade:
                after.append(p)
        # 若未精确匹配到交易价，则取所有价格作为参考
        if not after:
            after = price_series
        return after
