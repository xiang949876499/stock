"""SimulationEngine - 模拟交易核心引擎

协调 analysis -> signal -> execution -> recording 流程。
"""

import json
import uuid
from datetime import date, datetime
from typing import Optional

from src.infra.database import Database
from src.infra.logger import get_logger
from src.trading.strategy_selector import StrategySelector
from src.trading.mistake_analyzer import MistakeAnalyzer

logger = get_logger("simulation_engine")

INITIAL_CAPITAL = 1_000_000.0  # 100 万


class SimulationEngine:
    """模拟交易核心引擎"""

    def __init__(self, db: Database):
        self.db = db
        self.account_id = "sim_001"
        self._running = False
        self.strategy_selector = StrategySelector()
        self.mistake_analyzer = MistakeAnalyzer()
        self._rules_service = None
        self._init_account()

    def _get_rules_service(self):
        """延迟加载交易准则服务"""
        if self._rules_service is None:
            try:
                from src.trading_rules.service import TradingRuleService
                self._rules_service = TradingRuleService()
            except Exception as e:
                logger.warning(f"加载交易准则服务失败: {e}")
        return self._rules_service

    # ── 账户初始化 ──────────────────────────────────────────────────

    def _init_account(self):
        """创建模拟账户（如果不存在），初始资金 100 万"""
        existing = self.db.execute(
            "SELECT account_id FROM sim_accounts WHERE account_id = ?",
            (self.account_id,),
        ).fetchall()

        if not existing:
            self.db.execute(
                "INSERT INTO sim_accounts (account_id, initial_capital, balance, frozen, total_assets) "
                "VALUES (?, ?, ?, ?, ?)",
                (self.account_id, INITIAL_CAPITAL, INITIAL_CAPITAL, 0.0, INITIAL_CAPITAL),
            )
            self.db.commit()
            logger.info(f"创建模拟账户 {self.account_id}，初始资金 {INITIAL_CAPITAL}")

    # ── 账户查询 ────────────────────────────────────────────────────

    def _get_account(self) -> dict:
        """读取账户信息"""
        row = self.db.execute(
            "SELECT * FROM sim_accounts WHERE account_id = ?",
            (self.account_id,),
        ).fetchone()
        return dict(row)

    def _get_positions(self) -> list[dict]:
        """读取所有持仓"""
        rows = self.db.execute(
            "SELECT * FROM sim_positions WHERE account_id = ?",
            (self.account_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def _get_trades(self, trade_date: Optional[str] = None) -> list[dict]:
        """读取交易记录，可按日期过滤"""
        if trade_date:
            rows = self.db.execute(
                "SELECT * FROM sim_trades WHERE account_id = ? AND DATE(created_at) = ? ORDER BY created_at",
                (self.account_id, trade_date),
            ).fetchall()
        else:
            rows = self.db.execute(
                "SELECT * FROM sim_trades WHERE account_id = ? ORDER BY created_at",
                (self.account_id,),
            ).fetchall()
        return [dict(r) for r in rows]

    # ── 记录写入 ────────────────────────────────────────────────────

    def _record_analysis_log(
        self,
        symbol: str,
        strategy: str,
        score: float,
        signal: str,
        trend: str,
        reason: str,
        action_taken: str,
        action_reason: str,
        rule_checks: Optional[list[dict]] = None,
    ):
        """写入分析日志"""
        log_id = f"L-{uuid.uuid4().hex[:12]}"
        rule_checks_json = json.dumps(rule_checks, ensure_ascii=False) if rule_checks else None
        self.db.execute(
            "INSERT INTO sim_analysis_logs "
            "(log_id, account_id, symbol, strategy, score, signal, trend, reason, action_taken, action_reason, rule_checks) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (log_id, self.account_id, symbol, strategy, score, signal, trend, reason, action_taken, action_reason, rule_checks_json),
        )
        self.db.commit()

    def _record_trade(
        self,
        symbol: str,
        name: str,
        side: str,
        price: float,
        volume: int,
        amount: float,
        commission: float,
        strategy: Optional[str] = None,
        signal_score: Optional[float] = None,
        signal_reason: Optional[str] = None,
    ):
        """写入交易记录"""
        trade_id = f"T-{uuid.uuid4().hex[:12]}"
        self.db.execute(
            "INSERT INTO sim_trades "
            "(trade_id, account_id, symbol, name, side, price, volume, amount, commission, strategy, signal_score, signal_reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (trade_id, self.account_id, symbol, name, side, price, volume, amount, commission, strategy, signal_score, signal_reason),
        )
        self.db.commit()

    # ── 持仓更新 ────────────────────────────────────────────────────

    def _update_position(self, symbol: str, name: str, side: str, price: float, volume: int):
        """更新持仓（买入新增/加仓，卖出减仓/清仓）

        买入: 新增持仓或按成交量加权计算平均成本
        卖出: 减少持仓，成交量归零时删除
        """
        existing = self.db.execute(
            "SELECT * FROM sim_positions WHERE account_id = ? AND symbol = ?",
            (self.account_id, symbol),
        ).fetchone()

        if side == "BUY":
            if existing:
                # 加仓: 成交量加权平均成本
                old_volume = existing["volume"]
                old_cost = existing["avg_cost"]
                new_volume = old_volume + volume
                new_avg_cost = (old_cost * old_volume + price * volume) / new_volume

                self.db.execute(
                    "UPDATE sim_positions SET volume = ?, avg_cost = ?, updated_at = CURRENT_TIMESTAMP "
                    "WHERE account_id = ? AND symbol = ?",
                    (new_volume, new_avg_cost, self.account_id, symbol),
                )
            else:
                # 新增持仓
                today = date.today().isoformat()
                self.db.execute(
                    "INSERT INTO sim_positions "
                    "(account_id, symbol, name, volume, avg_cost, current_price, market_value, open_date) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (self.account_id, symbol, name, volume, price, price, price * volume, today),
                )
        elif side == "SELL":
            if not existing:
                logger.warning(f"卖出时未找到持仓: {symbol}")
                return

            remaining = existing["volume"] - volume
            if remaining <= 0:
                # 清仓
                self.db.execute(
                    "DELETE FROM sim_positions WHERE account_id = ? AND symbol = ?",
                    (self.account_id, symbol),
                )
            else:
                # 减仓
                self.db.execute(
                    "UPDATE sim_positions SET volume = ?, updated_at = CURRENT_TIMESTAMP "
                    "WHERE account_id = ? AND symbol = ?",
                    (remaining, self.account_id, symbol),
                )

        self.db.commit()

    # ── 账户余额更新 ────────────────────────────────────────────────

    def _update_account_balance(self, side: str, amount: float, commission: float):
        """更新账户余额

        BUY: 余额 -= (amount + commission)
        SELL: 余额 += (amount - commission)
        """
        if side == "BUY":
            self.db.execute(
                "UPDATE sim_accounts SET balance = balance - ?, updated_at = CURRENT_TIMESTAMP WHERE account_id = ?",
                (amount + commission, self.account_id),
            )
        elif side == "SELL":
            self.db.execute(
                "UPDATE sim_accounts SET balance = balance + ?, updated_at = CURRENT_TIMESTAMP WHERE account_id = ?",
                (amount - commission, self.account_id),
            )
        self.db.commit()

    def _update_total_assets(self):
        """更新总资产 = 余额 + sum(持仓市值)"""
        account = self._get_account()
        balance = account["balance"]

        rows = self.db.execute(
            "SELECT COALESCE(SUM(market_value), 0) as total_mv FROM sim_positions WHERE account_id = ?",
            (self.account_id,),
        ).fetchone()
        total_mv = rows["total_mv"]

        total_assets = balance + total_mv
        self.db.execute(
            "UPDATE sim_accounts SET total_assets = ?, updated_at = CURRENT_TIMESTAMP WHERE account_id = ?",
            (total_assets, self.account_id),
        )
        self.db.commit()

    # ── 引擎控制 ────────────────────────────────────────────────────

    def start(self):
        """启动引擎"""
        self._running = True
        logger.info("模拟交易引擎启动")

    def stop(self):
        """停止引擎"""
        self._running = False
        logger.info("模拟交易引擎停止")

    def is_running(self) -> bool:
        """引擎是否运行中"""
        return self._running

    def get_status(self) -> dict:
        """获取引擎状态"""
        return {
            "running": self._running,
            "account": self._get_account(),
            "positions": self._get_positions(),
        }

    # ── 准则检查 ────────────────────────────────────────────────────

    async def _check_rules(self, stock: dict, signal: str) -> list[dict]:
        """运行交易准则检查，返回检查结果列表

        Args:
            stock: 股票推荐数据（symbol, name, market, score）
            signal: AI 分析信号（buy/sell/hold）
        """
        rules_service = self._get_rules_service()
        if not rules_service:
            return []

        try:
            # 获取技术指标数据供准则检查器使用
            stock_data = await self._fetch_indicators(stock)
            if not stock_data:
                return []

            checker = rules_service.checker
            entry_results = checker.check_entry_rules(stock_data)
            exit_results = checker.check_exit_rules(stock_data)

            all_results = entry_results + exit_results
            return [
                {
                    "rule_id": r.rule_id,
                    "rule_title": r.rule_title,
                    "passed": r.passed,
                    "score": r.score,
                    "reason": r.reason,
                }
                for r in all_results
            ]
        except Exception as e:
            logger.warning(f"准则检查失败: {e}")
            return []

    async def _fetch_indicators(self, stock: dict) -> Optional[dict]:
        """获取股票技术指标，转换为准则检查器所需的格式"""
        try:
            from src.data.service import DataService
            from src.data.models import Market

            data_service = DataService()
            symbol = stock.get("symbol", "")
            market_str = stock.get("market", "A")
            market = Market(market_str)

            indicators = await data_service.get_technical_indicators(symbol, market)

            return {
                "symbol": symbol,
                "current_price": 0,
                "ma5": indicators.ma5,
                "ma10": indicators.ma10,
                "ma20": indicators.ma20,
                "ma60": indicators.ma60,
                "pe_ratio": 0,
                "volume": 0,
                "avg_volume": 0,
            }
        except Exception as e:
            logger.warning(f"获取 {stock.get('symbol')} 技术指标失败: {e}")
            return None

    # ── 分析周期 ────────────────────────────────────────────────────

    async def run_analysis_cycle(self):
        """执行一次盘中分析周期

        1. 获取推荐股票
        2. 对每只股票运行分析
        3. 记录分析日志
        """
        logger.info("开始盘中分析周期")

        # 获取推荐股票
        try:
            from src.analysis.strategies.stock_picker import get_stock_recommendations
            recommendations = await get_stock_recommendations("A", 10)
        except Exception as e:
            logger.warning(f"获取推荐失败: {e}")
            recommendations = []

        if not recommendations:
            logger.info("无推荐股票，跳过分析")
            return

        # 获取 AI 适配器
        ai_adapter = None
        try:
            from src.config import get_settings
            from src.analysis.ai.factory import AIModelFactory
            config = get_settings()
            ai_adapter = AIModelFactory.create(config)
        except Exception as e:
            logger.warning(f"AI 适配器初始化失败: {e}")

        # 逐只分析
        for stock in recommendations:
            symbol = stock.get("symbol", "")
            name = stock.get("name", symbol)
            strategy = self.strategy_selector.select([stock.get("score", 50)])

            try:
                if ai_adapter:
                    from src.analysis.service import AnalysisService
                    service = AnalysisService(ai_adapter)
                    result = await service.analyze_stock(symbol, strategy)

                    # 获取技术指标详情
                    tech_detail = await self._get_technical_detail(symbol)

                    # 运行准则检查
                    rule_checks = await self._check_rules(stock, result.signal)

                    # 生成详细分析理由
                    detailed_reason = self._build_detailed_reason(
                        result, tech_detail, rule_checks, stock
                    )

                    # 判断执行状态
                    if result.signal == "buy" and result.score >= 55:
                        action_taken = "executed"
                        action_reason = f"✅ 买入执行 | 评分 {result.score} ≥ 55 | {detailed_reason}"
                        self._execute_buy(symbol, name, result)
                    elif result.signal == "sell" and result.score <= 45:
                        action_taken = "executed"
                        action_reason = f"✅ 卖出执行 | 评分 {result.score} ≤ 45 | {detailed_reason}"
                        self._execute_sell(symbol, name, result)
                    elif result.signal == "buy":
                        action_taken = "skipped"
                        action_reason = f"⚠️ 买入信号但评分不足 ({result.score} < 55) | {detailed_reason}"
                    elif result.signal == "sell":
                        action_taken = "skipped"
                        action_reason = f"⚠️ 卖出信号但评分过高 ({result.score} > 45) | {detailed_reason}"
                    else:
                        action_taken = "skipped"
                        action_reason = f"⏸️ 持有观望 | {detailed_reason}"

                    # 记录分析日志
                    self._record_analysis_log(
                        symbol=symbol,
                        strategy=strategy,
                        score=result.score,
                        signal=result.signal,
                        trend=result.trend,
                        reason=result.reason,
                        action_taken=action_taken,
                        action_reason=action_reason,
                        rule_checks=rule_checks,
                    )

                    logger.info(f"分析完成: {symbol} {result.signal} ({result.score}分)")
                else:
                    # 无 AI，仅记录技术评分
                    self._record_analysis_log(
                        symbol=symbol,
                        strategy=strategy,
                        score=stock.get("score", 0),
                        signal="hold",
                        trend="neutral",
                        reason="AI 未配置，仅技术评分",
                        action_taken="skipped",
                        action_reason="AI 未配置，无法进行深度分析",
                    )

            except Exception as e:
                logger.error(f"分析 {symbol} 失败: {e}")
                self._record_analysis_log(
                    symbol=symbol,
                    strategy=strategy,
                    score=0,
                    signal="error",
                    trend="unknown",
                    reason=str(e),
                    action_taken="skipped",
                    action_reason=f"分析异常: {e}",
                )

        # 更新总资产
        self._update_total_assets()
        logger.info("盘中分析周期完成")

    def _build_detailed_reason(
        self, result, tech_detail: dict, rule_checks: list, stock: dict
    ) -> str:
        """构建详细的分析理由"""
        parts = []

        # 1. AI 分析摘要
        if result.reason:
            # 截取前 100 字符
            reason_brief = result.reason[:100] + "..." if len(result.reason) > 100 else result.reason
            parts.append(f"AI分析: {reason_brief}")

        # 2. 技术指标亮点
        if tech_detail:
            highlights = []
            ma = tech_detail.get("ma", {})
            macd = tech_detail.get("macd", {})
            rsi = tech_detail.get("rsi", {})
            volume = tech_detail.get("volume", {})

            # 均线判断
            if ma.get("ma5", 0) > ma.get("ma10", 0) > ma.get("ma20", 0):
                highlights.append("均线多头排列")
            elif ma.get("ma5", 0) < ma.get("ma10", 0) < ma.get("ma20", 0):
                highlights.append("均线空头排列")

            # MACD 判断
            if macd.get("macd", 0) > 0 and macd.get("macd_signal", 0) > 0:
                highlights.append("MACD金叉")
            elif macd.get("macd", 0) < 0:
                highlights.append("MACD死叉")

            # RSI 判断
            rsi_val = rsi.get("rsi_6", 50)
            if rsi_val < 30:
                highlights.append("RSI超卖")
            elif rsi_val > 70:
                highlights.append("RSI超买")

            # 成交量判断
            if volume.get("volume_ratio", 1) > 1.5:
                highlights.append("放量")
            elif volume.get("volume_ratio", 1) < 0.7:
                highlights.append("缩量")

            if highlights:
                parts.append(f"技术面: {', '.join(highlights)}")

        # 3. 准则检查结果
        if rule_checks:
            passed = [r for r in rule_checks if r.get("passed")]
            failed = [r for r in rule_checks if not r.get("passed")]
            if failed:
                failed_titles = [r.get("rule_title", "") for r in failed[:3]]
                parts.append(f"风险提示: {', '.join(failed_titles)}")
            if passed:
                passed_titles = [r.get("rule_title", "") for r in passed[:3]]
                parts.append(f"符合准则: {', '.join(passed_titles)}")

        return " | ".join(parts) if parts else "无详细分析"

    def _get_price(self, symbol: str) -> float:
        """获取股票当前价格"""
        try:
            from src.execution.gateways.simulated import get_current_price
            return get_current_price(symbol)
        except Exception as e:
            logger.warning(f"获取价格失败 {symbol}: {e}")
            return 0.0

    def _execute_buy(self, symbol: str, name: str, result):
        """执行买入"""
        # 检查是否已持有
        positions = self._get_positions()
        if any(p["symbol"] == symbol for p in positions):
            logger.info(f"已持有 {symbol}，跳过买入")
            return

        account = self._get_account()
        balance = account["balance"]
        # 动态分配资金：根据持仓数量调整
        position_count = len(positions)
        if position_count < 5:
            alloc_pct = 0.15  # 前 5 只各用 15%
        elif position_count < 10:
            alloc_pct = 0.08  # 6-10 只各用 8%
        else:
            alloc_pct = 0.05  # 10 只以上各用 5%

        buy_amount = balance * alloc_pct
        if buy_amount < 1000:
            logger.info(f"资金不足，跳过买入: {symbol}")
            return

        # 获取真实价格
        price = self._get_price(symbol)
        if price <= 0:
            logger.warning(f"无法获取价格，跳过买入: {symbol}")
            return

        volume = int(buy_amount / price / 100) * 100  # 取整到 100 股
        if volume <= 0:
            return

        actual_amount = price * volume
        commission = actual_amount * 0.0003

        self._update_account_balance("BUY", actual_amount, commission)
        self._update_position(symbol, name, "BUY", price, volume)
        self._record_trade(symbol, name, "BUY", price, volume, actual_amount, commission,
                           strategy=result.signal, signal_score=result.score, signal_reason=result.reason)
        logger.info(f"模拟买入: {symbol} {volume}股 @ {price}")

    def _execute_sell(self, symbol: str, name: str, result):
        """执行卖出"""
        positions = self._get_positions()
        pos = next((p for p in positions if p["symbol"] == symbol), None)
        if not pos:
            return

        # 获取真实价格，回退到持仓成本价
        price = self._get_price(symbol)
        if price <= 0:
            price = pos.get("avg_cost", 0)
        if price <= 0:
            logger.warning(f"无法获取价格，跳过卖出: {symbol}")
            return

        volume = pos["volume"]
        actual_amount = price * volume
        commission = actual_amount * 0.0003

        self._update_account_balance("SELL", actual_amount, commission)
        self._update_position(symbol, name, "SELL", price, volume)
        self._record_trade(symbol, name, "SELL", price, volume, actual_amount, commission,
                           strategy=result.signal, signal_score=result.score, signal_reason=result.reason)
        logger.info(f"模拟卖出: {symbol} {volume}股 @ {price}")
