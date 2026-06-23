"""SimulationEngine - 模拟交易核心引擎

协调 analysis -> signal -> execution -> recording 流程。
"""

import asyncio
import json
import uuid
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

from src.infra.database import Database
from src.infra.logger import get_logger
from src.trading.strategy_selector import StrategySelector
from src.trading.mistake_analyzer import MistakeAnalyzer
from src.trading.quant_policy import QuantLongTermPolicy, QuantDecision
from src.trading.reasoning import ReasoningSignal
from src.trading.thinking import (
    build_thinking_review,
    render_thinking_markdown,
    thinking_entry_to_signal_payload,
)

logger = get_logger("simulation_engine")

INITIAL_CAPITAL = 1_000_000.0  # 100 万


class SimulationEngine:
    """模拟交易核心引擎"""

    def __init__(self, db: Database):
        self.db = db
        self.account_id = "sim_001"
        self._running = False
        self._started_once = False
        self.strategy_selector = StrategySelector()
        self.mistake_analyzer = MistakeAnalyzer()
        self.long_term_policy = QuantLongTermPolicy()
        self.kronos_adapter = None
        self._kronos_adapter_initialized = False
        self.review_output_dir = Path("./data/simulation_reviews")
        self.thinking_output_dir = Path("./data/simulation_thinking")
        self._rules_service = None
        self._analysis_lock = asyncio.Lock()
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

    def _get_position_by_symbol(self, symbol: str) -> dict | None:
        """Return the current simulated position for a symbol, if any."""
        return next((p for p in self._get_positions() if p.get("symbol") == symbol), None)

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

    def _record_system_operation(self, action_taken: str, action_reason: str):
        """将引擎操作写入分析日志，供交易页面直接查看。"""
        self._record_analysis_log(
            symbol="SYSTEM",
            strategy="system",
            score=0,
            signal="info",
            trend="neutral",
            reason="模拟交易系统操作",
            action_taken=action_taken,
            action_reason=action_reason,
        )

    def _record_long_term_report(
        self,
        report_date: str,
        report_type: str,
        week_id: str,
        report_markdown: str,
        source_report_id: str | None = None,
        positions_snapshot: list[dict] | None = None,
        candidates_snapshot: list[dict] | None = None,
        metadata: dict | None = None,
    ) -> str:
        """写入长线 TradingAgents 报告，独立于每日交易报告。"""
        report_id = f"LT-{uuid.uuid4().hex[:12]}"
        self.db.execute(
            """
            INSERT OR REPLACE INTO sim_long_term_reports
            (
                report_id, account_id, report_date, report_type, week_id,
                source_report_id, positions_snapshot, candidates_snapshot,
                report_markdown, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report_id,
                self.account_id,
                report_date,
                report_type,
                week_id,
                source_report_id,
                json.dumps(positions_snapshot or [], ensure_ascii=False),
                json.dumps(candidates_snapshot or [], ensure_ascii=False),
                report_markdown,
                json.dumps(metadata or {}, ensure_ascii=False),
            ),
        )
        self.db.commit()
        return report_id

    def _get_long_term_reports(
        self,
        report_type: str | None = None,
        report_date: str | None = None,
    ) -> list[dict]:
        """读取长线报告列表。"""
        sql = "SELECT * FROM sim_long_term_reports WHERE account_id = ?"
        params: list = [self.account_id]
        if report_type:
            sql += " AND report_type = ?"
            params.append(report_type)
        if report_date:
            sql += " AND report_date = ?"
            params.append(report_date)
        sql += " ORDER BY report_date DESC, created_at DESC"
        rows = self.db.execute(sql, tuple(params)).fetchall()
        return [dict(r) for r in rows]

    def _get_latest_weekly_long_term_report(self, week_id: str | None = None) -> Optional[dict]:
        """读取最近一份周度 TradingAgents 长线报告。"""
        if week_id:
            row = self.db.execute(
                """
                SELECT * FROM sim_long_term_reports
                WHERE account_id = ? AND report_type = 'weekly_analysis' AND week_id = ?
                ORDER BY report_date DESC, created_at DESC
                LIMIT 1
                """,
                (self.account_id, week_id),
            ).fetchone()
        else:
            row = self.db.execute(
                """
                SELECT * FROM sim_long_term_reports
                WHERE account_id = ? AND report_type = 'weekly_analysis'
                ORDER BY report_date DESC, created_at DESC
                LIMIT 1
                """,
                (self.account_id,),
            ).fetchone()
        return dict(row) if row else None

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
        if self._running:
            return
        self._running = True
        self._started_once = True
        self._record_system_operation(
            action_taken="executed",
            action_reason="模拟交易引擎已启动，等待定时或手动分析",
        )
        logger.info("模拟交易引擎启动")

    def stop(self):
        """停止引擎"""
        if not self._running:
            return
        self._running = False
        self._record_system_operation(
            action_taken="executed",
            action_reason="模拟交易引擎已停止",
        )
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

    async def _get_technical_detail(self, symbol: str) -> dict:
        """获取股票技术指标详情，用于构建分析理由"""
        try:
            from src.data.service import DataService
            from src.data.models import Market
            from src.plugins.financial_analysis.technical_indicators import (
                calc_ma, calc_macd, calc_rsi, calc_volume_analysis,
            )

            data_service = DataService()
            market = Market.A  # 目前主要支持 A 股

            from datetime import date, timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=120)

            df = await data_service.get_daily(symbol, market, start_date, end_date)
            if df is None or df.empty:
                return {}

            closes = df["close"].tolist()
            volumes = df["volume"].tolist()

            ma_data = calc_ma(closes, [5, 10, 20, 60])
            macd_raw = calc_macd(closes)
            rsi_raw = calc_rsi(closes, [6, 12, 24])
            vol_raw = calc_volume_analysis(volumes, closes)

            # 映射为 _build_detailed_reason 期望的 key 格式
            macd_data = {
                "macd": macd_raw.get("macd", 0),
                "macd_signal": macd_raw.get("dif", 0),
            }
            rsi_data = {
                "rsi_6": rsi_raw.get("rsi6", 50),
            }
            vol_data = {
                "volume_ratio": vol_raw.get("volume_ratio_5", 1),
            }

            return {
                "ma": ma_data,
                "macd": macd_data,
                "rsi": rsi_data,
                "volume": vol_data,
            }
        except Exception as e:
            logger.warning(f"获取技术指标详情失败: {symbol}, {e}")
            return {}

    async def _fetch_news(self, symbol: str, limit: int = 5) -> list[dict]:
        """获取股票相关新闻

        Args:
            symbol: 股票代码
            limit: 获取新闻数量，默认 5 条

        Returns:
            [{"title": "...", "summary": "...", "sentiment": "positive/negative/neutral"}, ...]
        """
        try:
            from src.data.service import DataService
            from src.data.models import Market

            data_service = DataService()
            market = Market.A

            news_list = await data_service.get_news(symbol, market, limit=limit)
            if not news_list:
                return []

            result = []
            for news in news_list:
                result.append({
                    "title": news.title,
                    "summary": news.summary[:200] if news.summary else "",
                    "sentiment": getattr(news, "sentiment", "neutral"),
                    "publish_time": str(news.publish_time) if news.publish_time else "",
                })

            logger.info(f"获取新闻: {symbol}, {len(result)} 条")
            return result

        except Exception as e:
            logger.warning(f"获取新闻失败: {symbol}, {e}")
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

    async def run_analysis_cycle(self, analysis_date: date | str | None = None):
        """串行执行长线分析周期，避免手动任务与调度任务重叠。"""
        if self._analysis_lock.locked():
            message = "已有分析周期正在运行，本次请求已跳过"
            self._record_system_operation(
                action_taken="skipped",
                action_reason=message,
            )
            return {"status": "skipped", "message": message}

        async with self._analysis_lock:
            return await self.run_short_term_kline_monitor()

    async def run_short_term_kline_monitor(self):
        """Monitor short-term K-line signals and execute simulated intraday trades."""
        logger.info("开始短线 K 线监控周期")
        self._record_system_operation(
            action_taken="executed",
            action_reason="开始短线 K 线监控周期，正在筛选候选股并读取技术指标",
        )

        try:
            from src.analysis.strategies.stock_picker import get_stock_recommendations

            recommendations = await get_stock_recommendations(
                "A",
                10,
                use_ai_screen=False,
                progress_callback=lambda message: self._record_system_operation(
                    action_taken="executed",
                    action_reason=message,
                ),
            )
        except Exception as e:
            logger.warning(f"获取短线候选失败: {e}")
            self._record_system_operation(
                action_taken="skipped",
                action_reason=f"短线候选股票筛选失败：{e}",
            )
            recommendations = []

        if not recommendations:
            self._record_system_operation(
                action_taken="skipped",
                action_reason="本轮 K 线监控未产生候选股票，未执行买卖操作",
            )
            return {
                "status": "completed",
                "mode": "short_term_kline",
                "recommendations": 0,
                "trades": 0,
            }

        for stock in recommendations:
            symbol = stock.get("symbol", "")
            name = stock.get("name", symbol)
            try:
                news_list = await self._fetch_news(symbol, limit=3)
                tech_detail = await self._get_technical_detail(symbol)
                decision = self._short_term_kline_decision(stock, tech_detail, news_list)
                rule_checks = await self._check_rules(stock, decision.signal)

                if any(not item.get("passed") for item in rule_checks):
                    decision.signal = "hold"
                    decision.trend = "neutral"
                    decision.score = min(decision.score, 54)
                    decision.reason += " 交易准则存在阻断项，短线信号降级为观望。"

                if decision.signal == "buy" and decision.score >= 60:
                    executed, execution_reason = self._execute_buy(symbol, name, decision)
                    action_taken = "executed" if executed else "skipped"
                    action_reason = (
                        f"短线K线买入{'执行' if executed else '未执行'}：{execution_reason} | "
                        f"{decision.reason}"
                    )
                elif decision.signal == "sell" and decision.score <= 42:
                    executed, execution_reason = self._execute_sell(symbol, name, decision)
                    action_taken = "executed" if executed else "skipped"
                    action_reason = (
                        f"短线K线卖出{'执行' if executed else '未执行'}：{execution_reason} | "
                        f"{decision.reason}"
                    )
                else:
                    action_taken = "skipped"
                    action_reason = f"短线K线保持观察 | {decision.reason}"

                self._record_analysis_log(
                    symbol=symbol,
                    strategy="short_term_kline",
                    score=decision.score,
                    signal=decision.signal,
                    trend=decision.trend,
                    reason=decision.reason,
                    action_taken=action_taken,
                    action_reason=action_reason,
                    rule_checks=rule_checks,
                )
            except Exception as e:
                logger.error(f"短线 K 线监控失败: {symbol}, {e}")
                self._record_analysis_log(
                    symbol=symbol,
                    strategy="short_term_kline",
                    score=0,
                    signal="error",
                    trend="unknown",
                    reason=str(e),
                    action_taken="skipped",
                    action_reason=f"短线 K 线监控异常: {e}",
                )

        self._update_total_assets()
        trade_count = len(self._get_trades(date.today().isoformat()))
        self._record_system_operation(
            action_taken="executed",
            action_reason=(
                f"短线 K 线监控完成：检查 {len(recommendations)} 只候选股，"
                f"今日累计成交 {trade_count} 笔"
            ),
        )
        return {
            "status": "completed",
            "mode": "short_term_kline",
            "recommendations": len(recommendations),
            "trades": trade_count,
        }

    @staticmethod
    def _coerce_analysis_date(value: date | str | None) -> date:
        if value is None:
            return date.today()
        if isinstance(value, date):
            return value
        return date.fromisoformat(value)

    @staticmethod
    def _week_id(value: date) -> str:
        iso = value.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"

    async def run_weekly_quant_analysis(self, analysis_date: date | None = None):
        """Create a deterministic quant baseline for the long-term simulation plan."""
        current_date = analysis_date or date.today()
        report_date = current_date.isoformat()
        week_id = self._week_id(current_date)

        logger.info("开始量化长线周计划")
        self._record_system_operation(
            action_taken="executed",
            action_reason="开始长线周计划：使用量化筛选、技术面、新闻和交易准则生成候选基准",
        )

        try:
            from src.analysis.strategies.stock_picker import get_stock_recommendations

            recommendations = await get_stock_recommendations(
                "A",
                5,
                use_ai_screen=False,
                progress_callback=lambda message: self._record_system_operation(
                    action_taken="executed",
                    action_reason=message,
                ),
            )
        except Exception as e:
            logger.warning(f"获取量化长线候选失败: {e}")
            recommendations = []

        decisions: list[dict] = []
        for stock in recommendations:
            symbol = stock.get("symbol", "")
            try:
                news_list = await self._fetch_news(symbol, limit=5)
            except Exception as exc:
                logger.warning(f"量化周计划新闻获取失败: {symbol}, {exc}")
                news_list = []
            try:
                tech_detail = await self._get_technical_detail(symbol)
            except Exception as exc:
                logger.warning(f"量化周计划技术指标获取失败: {symbol}, {exc}")
                tech_detail = {}

            quant_candidate = self._build_quant_baseline_candidate(
                stock=stock,
                report_date=report_date,
                news_list=news_list,
                tech_detail=tech_detail,
            )

            try:
                rule_checks = await self._check_rules(stock, quant_candidate["signal"])
            except Exception as exc:
                logger.warning(f"量化周计划准则检查失败: {symbol}, {exc}")
                rule_checks = []

            if any(not item.get("passed") for item in rule_checks):
                quant_candidate["score"] = min(float(quant_candidate["score"]), 55.0)
                quant_candidate["signal"] = "hold"
                quant_candidate["trend"] = "neutral"
                quant_candidate.setdefault("risks", []).append("blocking_rules")
                quant_candidate["reason"] += " 交易准则存在阻断项，候选降级为观察。"

            current_price = self._get_price(symbol)
            quant_candidate["price"] = current_price
            quant_candidate["rule_checks"] = rule_checks
            quant_candidate["reasoning_signals"] = [
                ReasoningSignal.from_candidate(quant_candidate).to_dict()
            ]

            self._record_analysis_log(
                symbol=symbol,
                strategy="quant_long_term_baseline",
                score=quant_candidate["score"],
                signal=quant_candidate["signal"],
                trend=quant_candidate["trend"],
                reason=quant_candidate["reason"],
                action_taken=quant_candidate["action_taken"],
                action_reason=quant_candidate["action_reason"],
                rule_checks=rule_checks,
            )
            decisions.append(quant_candidate)

        self._update_total_assets()
        markdown = self._build_quant_weekly_long_term_report(report_date, week_id, decisions)
        report_id = self._record_long_term_report(
            report_date=report_date,
            report_type="weekly_analysis",
            week_id=week_id,
            report_markdown=markdown,
            positions_snapshot=self._get_positions(),
            candidates_snapshot=decisions,
            metadata={"strategy": "quant_long_term_baseline", "horizon": "long_term"},
        )
        self._record_system_operation(
            action_taken="executed",
            action_reason=f"量化长线周计划完成：生成 {week_id} Quant 报告",
        )
        return {
            "status": "completed",
            "mode": "weekly_quant_long_term",
            "report_type": "weekly_analysis",
            "report_id": report_id,
            "recommendations": len(recommendations),
            "trades": 0,
        }

    def _build_quant_baseline_candidate(
        self,
        stock: dict,
        report_date: str,
        news_list: list[dict],
        tech_detail: dict,
    ) -> dict:
        symbol = stock.get("symbol", "")
        name = stock.get("name", symbol)
        market = stock.get("market", "A")
        score = max(0.0, min(100.0, float(stock.get("score") or 50.0)))
        risks: list[str] = []
        evidence: dict = {
            "screen_score": stock.get("score"),
            "market": market,
            "analysis_date": report_date,
        }

        ma = tech_detail.get("ma", {}) if tech_detail else {}
        if ma:
            evidence["ma"] = ma
            ma5 = float(ma.get("ma5") or 0)
            ma20 = float(ma.get("ma20") or 0)
            if ma5 > ma20:
                score += 4
            elif ma5 < ma20:
                score -= 6
                risks.append("weak_momentum")

        positive_news = sum(1 for item in news_list if item.get("sentiment") == "positive")
        negative_news = sum(1 for item in news_list if item.get("sentiment") == "negative")
        evidence["news_balance"] = {"positive": positive_news, "negative": negative_news}
        if negative_news > positive_news:
            score -= 5
            risks.append("negative_news")
        elif positive_news > negative_news:
            score += 3

        score = max(0.0, min(100.0, round(score, 2)))
        if score >= self.long_term_policy.buy_score_threshold:
            signal = "buy"
            trend = "bullish"
        elif score <= self.long_term_policy.sell_score_threshold:
            signal = "sell"
            trend = "bearish"
        else:
            signal = "hold"
            trend = "neutral"

        reason = (
            f"Quant baseline score {score:.2f}: technical screen {float(stock.get('score') or 50):.2f}, "
            f"news balance +{positive_news}/-{negative_news}."
        )
        if risks:
            reason += f" Risk flags: {', '.join(risks)}."

        return {
            "symbol": symbol,
            "name": name,
            "market": market,
            "provider": "quant_screen",
            "signal": signal,
            "score": score,
            "trend": trend,
            "confidence": 0.72,
            "price": 0.0,
            "action_taken": "researched",
            "action_reason": (
                "量化长线候选基准已记录，模拟买卖由每日 QuantLongTermPolicy 统一执行"
            ),
            "reason": reason,
            "risks": risks,
            "evidence": evidence,
        }

    def _short_term_kline_decision(
        self,
        stock: dict,
        tech_detail: dict,
        news_list: list[dict],
    ):
        base_score = float(stock.get("score") or 50)
        score = base_score
        risks: list[str] = []
        signals: list[str] = []

        ma = tech_detail.get("ma", {}) if tech_detail else {}
        ma5 = float(ma.get("ma5") or 0)
        ma10 = float(ma.get("ma10") or 0)
        ma20 = float(ma.get("ma20") or 0)
        if ma5 and ma10 and ma20:
            if ma5 > ma10 > ma20:
                score += 8
                signals.append("MA5>MA10>MA20")
            elif ma5 < ma10 < ma20:
                score -= 10
                risks.append("ma_short_bearish")
            elif ma5 < ma20:
                score -= 5
                risks.append("ma5_below_ma20")

        macd = tech_detail.get("macd", {}) if tech_detail else {}
        macd_value = float(macd.get("macd") or 0)
        macd_signal = float(macd.get("macd_signal") or 0)
        if macd_value > macd_signal:
            score += 5
            signals.append("macd_above_signal")
        elif macd_value < macd_signal:
            score -= 5
            risks.append("macd_below_signal")

        rsi = tech_detail.get("rsi", {}) if tech_detail else {}
        rsi6 = float(rsi.get("rsi_6") or 50)
        if rsi6 >= 78:
            score -= 8
            risks.append("rsi_overbought")
        elif 45 <= rsi6 <= 68:
            score += 4
            signals.append("rsi_healthy")
        elif rsi6 <= 30:
            score -= 5
            risks.append("rsi_weak")

        volume = tech_detail.get("volume", {}) if tech_detail else {}
        volume_ratio = float(volume.get("volume_ratio") or 1)
        if 1.2 <= volume_ratio <= 2.5:
            score += 3
            signals.append("volume_confirmed")
        elif volume_ratio >= 3:
            score -= 3
            risks.append("volume_spike")

        negative_news = sum(1 for item in news_list if item.get("sentiment") == "negative")
        positive_news = sum(1 for item in news_list if item.get("sentiment") == "positive")
        if negative_news > positive_news:
            score -= 5
            risks.append("negative_news")
        elif positive_news > negative_news:
            score += 3
            signals.append("positive_news")

        score = max(0.0, min(100.0, round(score, 2)))
        if score >= 60 and "rsi_overbought" not in risks:
            signal = "buy"
            trend = "bullish"
        elif score <= 42 or any(
            risk in risks for risk in ("ma_short_bearish", "macd_below_signal")
        ):
            signal = "sell"
            trend = "bearish"
        else:
            signal = "hold"
            trend = "neutral"

        reason = (
            f"Short-term K-line score {score:.2f}, base screen {base_score:.2f}. "
            f"Signals: {', '.join(signals) or 'none'}. "
            f"Risks: {', '.join(risks) or 'none'}."
        )
        return SimpleNamespace(
            score=score,
            signal=signal,
            trend=trend,
            reason=reason,
        )

    async def run_weekly_tradingagents_analysis(self, analysis_date: date | None = None):
        """每周使用 TradingAgents 进行偏长线分析。"""
        current_date = analysis_date or date.today()
        report_date = current_date.isoformat()
        week_id = self._week_id(current_date)

        logger.info("开始 TradingAgents 长线周分析")
        self._record_system_operation(
            action_taken="executed",
            action_reason="开始长线周分析：使用 TradingAgents 筛选并评估候选股",
        )

        try:
            from src.analysis.strategies.stock_picker import get_stock_recommendations

            recommendations = await get_stock_recommendations(
                "A",
                5,
                use_ai_screen=False,
                progress_callback=lambda message: self._record_system_operation(
                    action_taken="executed",
                    action_reason=message,
                ),
            )
        except Exception as e:
            logger.warning(f"获取长线候选失败: {e}")
            recommendations = []

        decisions: list[dict] = []
        from src.analysis.service import AnalysisService

        service = AnalysisService(ai_adapter=None)
        for stock in recommendations:
            symbol = stock.get("symbol", "")
            name = stock.get("name", symbol)
            market = stock.get("market", "A")
            try:
                result = await service.analyze_stock(
                    symbol,
                    "tradingagents",
                    context={
                        "market": market,
                        "analysis_date": report_date,
                        "horizon": "long_term",
                        "simulation_mode": "weekly_long_term",
                    },
                )
                news_list = await self._fetch_news(symbol, limit=5)
                tech_detail = await self._get_technical_detail(symbol)
                rule_checks = await self._check_rules(stock, result.signal)
                detailed_reason = self._build_detailed_reason(
                    result, tech_detail, rule_checks, stock, news_list
                )

                current_price = self._get_price(symbol)
                action_taken = "researched"
                action_reason = (
                    "长线周度研究基准已记录，模拟买卖将由每日量化策略统一执行 | "
                    f"{detailed_reason}"
                )
                reasoning_signal = ReasoningSignal(
                    provider="tradingagents",
                    symbol=symbol,
                    name=name,
                    signal=result.signal,
                    score=result.score,
                    confidence=0.75,
                    rationale=result.reason,
                    evidence={
                        "trend": result.trend,
                        "market": market,
                        "analysis_date": report_date,
                    },
                )

                self._record_analysis_log(
                    symbol=symbol,
                    strategy="tradingagents_long_term",
                    score=result.score,
                    signal=result.signal,
                    trend=result.trend,
                    reason=result.reason,
                    action_taken=action_taken,
                    action_reason=action_reason,
                    rule_checks=rule_checks,
                )
                decisions.append(
                    {
                        "symbol": symbol,
                        "name": name,
                        "market": market,
                        "signal": result.signal,
                        "score": result.score,
                        "trend": result.trend,
                        "price": current_price,
                        "action_taken": action_taken,
                        "action_reason": action_reason,
                        "reason": result.reason,
                        "reasoning_signals": [reasoning_signal.to_dict()],
                    }
                )
            except Exception as e:
                if self._is_transient_external_error(e):
                    logger.warning(f"TradingAgents 外部连接中断: {symbol}, {e}")
                    current_price = self._get_price(symbol)
                    reason = f"外部连接中断，暂按持有观察处理: {e}"
                    self._record_analysis_log(
                        symbol=symbol,
                        strategy="tradingagents_long_term",
                        score=50,
                        signal="hold",
                        trend="neutral",
                        reason=reason,
                        action_taken="skipped",
                        action_reason=reason,
                    )
                    decisions.append(
                        {
                            "symbol": symbol,
                            "name": name,
                            "market": market,
                            "signal": "hold",
                            "score": 50,
                            "trend": "neutral",
                            "price": current_price,
                            "action_taken": "skipped",
                            "action_reason": reason,
                            "reason": reason,
                            "transient_error": True,
                        }
                    )
                    continue

                logger.error(f"TradingAgents 长线分析失败: {symbol}, {e}")
                self._record_analysis_log(
                    symbol=symbol,
                    strategy="tradingagents_long_term",
                    score=0,
                    signal="error",
                    trend="unknown",
                    reason=str(e),
                    action_taken="skipped",
                    action_reason=f"TradingAgents 长线分析异常: {e}",
                )
                decisions.append(
                    {
                        "symbol": symbol,
                        "name": name,
                        "market": market,
                        "signal": "error",
                        "score": 0,
                        "trend": "unknown",
                        "price": self._get_price(symbol),
                        "action_taken": "skipped",
                        "action_reason": str(e),
                        "reason": str(e),
                    }
                )

        self._update_total_assets()
        markdown = self._build_weekly_long_term_report(report_date, week_id, decisions)
        report_id = self._record_long_term_report(
            report_date=report_date,
            report_type="weekly_analysis",
            week_id=week_id,
            report_markdown=markdown,
            positions_snapshot=self._get_positions(),
            candidates_snapshot=decisions,
            metadata={"strategy": "tradingagents_long_term", "horizon": "long_term"},
        )
        self._record_system_operation(
            action_taken="executed",
            action_reason=f"长线周分析完成：生成 {week_id} TradingAgents 报告",
        )
        return {
            "status": "completed",
            "mode": "weekly_long_term",
            "report_type": "weekly_analysis",
            "report_id": report_id,
            "recommendations": len(recommendations),
            "trades": 0,
        }

    @staticmethod
    def _is_transient_external_error(error: Exception) -> bool:
        """Detect network/provider disconnects that should not poison weekly baselines."""
        text = f"{type(error).__name__}: {error}".lower()
        transient_markers = (
            "connection aborted",
            "connectionreseterror",
            "connection reset",
            "remote end closed connection",
            "remotedisconnected",
            "timed out",
            "timeout",
            "temporarily unavailable",
            "server disconnected",
        )
        return any(marker in text for marker in transient_markers)

    async def run_daily_long_term_validation(self, analysis_date: date | None = None):
        """每天验证最近一份量化周计划结果。"""
        current_date = analysis_date or date.today()
        report_date = current_date.isoformat()
        week_id = self._week_id(current_date)
        weekly_report = (
            self._get_latest_weekly_long_term_report(week_id)
            or self._get_latest_weekly_long_term_report()
        )
        if not weekly_report:
            return await self.run_weekly_quant_analysis(current_date)

        candidates = json.loads(weekly_report.get("candidates_snapshot") or "[]")
        validations = []
        for candidate in candidates:
            symbol = candidate.get("symbol", "")
            current_price = self._get_price(symbol)
            baseline_price = candidate.get("price") or 0
            change_pct = (
                (current_price - baseline_price) / baseline_price
                if baseline_price and current_price
                else 0
            )
            validations.append(
                {
                    "symbol": symbol,
                    "name": candidate.get("name", symbol),
                    "signal": candidate.get("signal", "hold"),
                    "score": candidate.get("score", 0),
                    "baseline_price": baseline_price,
                    "current_price": current_price,
                    "change_pct": change_pct,
                    "status": self._validation_status(candidate, change_pct),
                }
            )

        markdown = self._build_daily_validation_report(
            report_date,
            week_id,
            weekly_report,
            validations,
        )
        validation_report_id = self._record_long_term_report(
            report_date=report_date,
            report_type="daily_validation",
            week_id=week_id,
            source_report_id=weekly_report["report_id"],
            report_markdown=markdown,
            positions_snapshot=self._get_positions(),
            candidates_snapshot=validations,
            metadata={"source_weekly_report_id": weekly_report["report_id"]},
        )
        self._record_system_operation(
            action_taken="executed",
            action_reason=f"长线每日验证完成：验证 {len(validations)} 条量化周度结论",
        )
        optimizations = await self._build_daily_optimizations(
            report_date,
            weekly_report,
            validations,
        )
        optimization_markdown = self._build_daily_optimization_report(
            report_date,
            week_id,
            weekly_report,
            optimizations,
        )
        artifact_payload = {
            "report_date": report_date,
            "week_id": week_id,
            "source_weekly_report_id": weekly_report["report_id"],
            "validation_report_id": validation_report_id,
            "optimizations": optimizations,
        }
        artifacts = self._save_optimization_artifacts(
            report_date,
            optimization_markdown,
            artifact_payload,
        )
        thinking_review = build_thinking_review(report_date, optimizations)
        thinking_artifacts = self._save_thinking_artifacts(
            report_date,
            thinking_review,
        )
        optimization_report_id = self._record_long_term_report(
            report_date=report_date,
            report_type="daily_optimization",
            week_id=week_id,
            source_report_id=weekly_report["report_id"],
            report_markdown=optimization_markdown,
            positions_snapshot=self._get_positions(),
            candidates_snapshot=optimizations,
            metadata={
                "source_weekly_report_id": weekly_report["report_id"],
                "validation_report_id": validation_report_id,
                "artifacts": artifacts,
                "thinking_artifacts": thinking_artifacts,
            },
        )
        self._record_system_operation(
            action_taken="executed",
            action_reason=f"Daily quant optimization archived: {len(optimizations)} symbols",
        )
        return {
            "status": "completed",
            "mode": "daily_optimization",
            "report_type": "daily_optimization",
            "report_id": optimization_report_id,
            "validation_report_id": validation_report_id,
            "validated": len(validations),
            "optimized": len(optimizations),
            "artifacts": artifacts,
            "thinking_artifacts": thinking_artifacts,
        }

    async def _build_daily_optimizations(
        self,
        report_date: str,
        weekly_report: dict,
        validations: list[dict],
    ) -> list[dict]:
        """Build daily optimization rows from the weekly quant baseline."""
        candidates = json.loads(weekly_report.get("candidates_snapshot") or "[]")
        candidates = await self._enrich_candidates_with_kronos(
            candidates,
            self._coerce_analysis_date(report_date),
        )
        validation_by_symbol = {item.get("symbol"): item for item in validations}
        optimizations = []

        for candidate in candidates:
            symbol = candidate.get("symbol", "")
            validation = validation_by_symbol.get(symbol, {})
            signal = candidate.get("signal", "hold")

            try:
                news_list = await self._fetch_news(symbol, limit=5)
            except Exception as exc:
                logger.warning(f"Daily optimization news fetch failed: {symbol}, {exc}")
                news_list = []

            try:
                tech_detail = await self._get_technical_detail(symbol)
            except Exception as exc:
                logger.warning(f"Daily optimization technical fetch failed: {symbol}, {exc}")
                tech_detail = {}

            try:
                rule_checks = await self._check_rules(candidate, signal)
            except Exception as exc:
                logger.warning(f"Daily optimization rule check failed: {symbol}, {exc}")
                rule_checks = []

            position = self._get_position_by_symbol(symbol)
            baseline_price = validation.get("baseline_price", candidate.get("price") or 0)
            current_price = validation.get("current_price", 0)
            reasoning_signals = self._build_reasoning_signals(
                candidate=candidate,
                validation=validation,
                news_list=news_list,
                tech_detail=tech_detail,
                rule_checks=rule_checks,
            )
            thinking_signal = self._thinking_reasoning_signal(
                symbol,
                candidate.get("name", symbol),
                report_date,
            )
            if thinking_signal:
                reasoning_signals.append(thinking_signal)
            decision = self.long_term_policy.decide(
                symbol=symbol,
                name=candidate.get("name", symbol),
                current_price=float(current_price or 0),
                baseline_price=float(baseline_price or 0),
                position=position,
                rule_checks=rule_checks,
                signals=reasoning_signals,
            )
            action_taken, action_reason = self._execute_quant_decision(
                candidate,
                decision,
            )
            self._record_analysis_log(
                symbol=symbol,
                strategy="quant_long_term",
                score=decision.score,
                signal=decision.signal,
                trend="neutral",
                reason=decision.rationale,
                action_taken=action_taken,
                action_reason=action_reason,
                rule_checks=rule_checks,
            )
            optimizations.append(
                {
                    "symbol": symbol,
                    "name": candidate.get("name", symbol),
                    "weekly_signal": signal,
                    "weekly_score": candidate.get("score", 0),
                    "baseline_price": baseline_price,
                    "current_price": current_price,
                    "change_pct": validation.get("change_pct", 0),
                    "validation_status": validation.get("status", ""),
                    "action": decision.action,
                    "quant_signal": decision.signal,
                    "quant_score": decision.score,
                    "target_weight": decision.target_weight,
                    "allocation_pct": decision.allocation_pct,
                    "executable": decision.executable,
                    "risk_flags": decision.risk_flags,
                    "rationale": decision.rationale,
                    "execution": {
                        "action_taken": action_taken,
                        "action_reason": action_reason,
                    },
                    "reasoning_signals": [signal.to_dict() for signal in reasoning_signals],
                    "provider_breakdown": decision.provider_breakdown,
                    "daily_changes": {
                        "news": news_list,
                        "technical": tech_detail,
                        "rule_checks": rule_checks,
                        "position": position,
                    },
                    "source_weekly_report_id": weekly_report.get("report_id"),
                    "report_date": report_date,
                }
            )

        return optimizations


    def _thinking_reasoning_signal(
        self,
        symbol: str,
        name: str,
        report_date: str,
    ) -> ReasoningSignal | None:
        entry = self._load_latest_thinking_entry(symbol, report_date)
        if not entry:
            return None
        payload = thinking_entry_to_signal_payload(entry)
        if not payload:
            return None
        return ReasoningSignal(
            provider="thinking",
            symbol=symbol,
            name=name,
            signal=str(payload.get("signal") or "hold"),
            score=float(payload.get("score") or 50),
            confidence=float(payload.get("confidence") or 0.5),
            rationale=str(payload.get("rationale") or ""),
            risks=list(payload.get("risks") or []),
            evidence=dict(payload.get("evidence") or {}),
            artifact_paths=list(payload.get("artifact_paths") or []),
        )

    def _load_latest_thinking_entry(
        self,
        symbol: str,
        before_report_date: str,
    ) -> dict | None:
        try:
            if not self.thinking_output_dir.exists():
                return None
            date_dirs = sorted(
                (
                    item
                    for item in self.thinking_output_dir.iterdir()
                    if item.is_dir() and item.name < before_report_date
                ),
                key=lambda item: item.name,
                reverse=True,
            )
            for date_dir in date_dirs:
                json_path = date_dir / "thinking.json"
                if not json_path.exists():
                    continue
                payload = json.loads(json_path.read_text(encoding="utf-8"))
                for entry in payload.get("entries", []):
                    if str(entry.get("symbol") or "") == symbol:
                        result = dict(entry)
                        result["artifact_paths"] = [str(json_path)]
                        return result
        except Exception as exc:
            logger.warning(f"Thinking feedback load failed: {symbol}, {exc}")
        return None

    async def _enrich_candidates_with_kronos(
        self,
        candidates: list[dict],
        analysis_date: date,
    ) -> list[dict]:
        adapter = self._get_kronos_adapter()
        if adapter is None:
            return candidates

        enriched = []
        for candidate in candidates:
            item = dict(candidate)
            if self._candidate_has_kronos(item):
                enriched.append(item)
                continue
            try:
                prediction = await adapter.summarize_candidate(item, analysis_date)
            except Exception as exc:
                logger.warning(
                    f"Kronos forecast generation failed: {item.get('symbol', '')}, {exc}"
                )
                prediction = None
            if prediction:
                item["kronos_prediction"] = prediction
            enriched.append(item)
        return enriched

    def _get_kronos_adapter(self):
        if self.kronos_adapter is not None:
            return self.kronos_adapter
        if self._kronos_adapter_initialized:
            return None
        self._kronos_adapter_initialized = True
        try:
            from src.trading.kronos_adapter import KronosAdapter

            adapter = KronosAdapter()
            if not adapter.enabled:
                return None
            self.kronos_adapter = adapter
            return self.kronos_adapter
        except Exception as exc:
            logger.warning(f"Kronos adapter unavailable: {exc}")
            return None

    @staticmethod
    def _candidate_has_kronos(candidate: dict) -> bool:
        return any(
            isinstance(candidate.get(key), dict)
            for key in ("kronos_prediction", "kronos_signal", "kronos")
        )

    def _build_reasoning_signals(
        self,
        candidate: dict,
        validation: dict,
        news_list: list[dict],
        tech_detail: dict,
        rule_checks: list[dict],
    ) -> list[ReasoningSignal]:
        """Create normalized signals from TradingAgents, Vibe, technicals, and rules."""
        signals = [ReasoningSignal.from_candidate(candidate)]
        vibe_signal = self._extract_vibe_trading_signal(candidate)
        if vibe_signal:
            signals.append(vibe_signal)
        kronos_signal = self._extract_kronos_signal(candidate)
        if kronos_signal:
            signals.append(kronos_signal)
        technical_signal = self._technical_reasoning_signal(candidate, validation, tech_detail, news_list)
        if technical_signal:
            signals.append(technical_signal)
        rules_signal = self._rules_reasoning_signal(candidate, rule_checks)
        if rules_signal:
            signals.append(rules_signal)
        return signals

    @staticmethod
    def _extract_vibe_trading_signal(candidate: dict) -> ReasoningSignal | None:
        """Read optional Vibe-Trading evidence stored on a candidate snapshot."""
        vibe = candidate.get("vibe_trading") or candidate.get("vibe_signal")
        if not isinstance(vibe, dict):
            return None
        signal = vibe.get("signal") or vibe.get("action") or "hold"
        score = float(vibe.get("score") or vibe.get("confidence_score") or 50)
        risks = list(vibe.get("risks") or [])
        metrics = vibe.get("backtest") or vibe.get("metrics") or {}
        if isinstance(metrics, dict):
            if float(metrics.get("sharpe", 0) or 0) < 0:
                risks.append("negative_backtest")
            if float(metrics.get("max_drawdown", 0) or 0) <= -0.15:
                risks.append("high_backtest_drawdown")
        return ReasoningSignal(
            provider="vibe_trading",
            symbol=str(candidate.get("symbol") or ""),
            name=str(candidate.get("name") or candidate.get("symbol") or ""),
            signal=str(signal),
            score=score,
            confidence=float(vibe.get("confidence") or 0.75),
            rationale=str(vibe.get("rationale") or vibe.get("reason") or "Vibe-Trading evidence"),
            risks=risks,
            evidence={"metrics": metrics, "source": vibe.get("source", "candidate_snapshot")},
            artifact_paths=list(vibe.get("artifact_paths") or []),
        )

    @staticmethod
    def _extract_kronos_signal(candidate: dict) -> ReasoningSignal | None:
        """Read optional Kronos forecast evidence stored on a candidate snapshot."""
        kronos = (
            candidate.get("kronos_prediction")
            or candidate.get("kronos_signal")
            or candidate.get("kronos")
        )
        if not isinstance(kronos, dict):
            return None

        forecast_return = SimulationEngine._first_float(
            kronos,
            ("forecast_return", "expected_return", "predicted_return"),
        )
        current_price = (
            SimulationEngine._optional_float(kronos["current_price"])
            if "current_price" in kronos
            else SimulationEngine._optional_float(candidate.get("price"))
        )
        predicted_close = SimulationEngine._first_float(
            kronos,
            ("predicted_close", "forecast_close"),
        )
        if forecast_return is None and current_price and predicted_close:
            forecast_return = (predicted_close - current_price) / current_price

        signal = kronos.get("signal") or kronos.get("action")
        if not signal:
            if forecast_return is not None and forecast_return <= -0.03:
                signal = "sell"
            elif forecast_return is not None and forecast_return >= 0.03:
                signal = "buy"
            else:
                signal = "hold"

        score = SimulationEngine._optional_float(kronos.get("score"))
        if score is None:
            score = 50.0
            if forecast_return is not None:
                score = max(0.0, min(100.0, 50.0 + forecast_return * 300.0))

        risks = list(kronos.get("risks") or [])
        if signal == "sell" and "kronos_bearish_forecast" not in risks:
            risks.append("kronos_bearish_forecast")

        evidence = {
            "forecast_return": forecast_return,
            "predicted_close": predicted_close,
            "current_price": current_price,
            "horizon": kronos.get("horizon"),
            "source": kronos.get("source", "candidate_snapshot"),
        }

        return ReasoningSignal(
            provider="kronos",
            symbol=str(candidate.get("symbol") or ""),
            name=str(candidate.get("name") or candidate.get("symbol") or ""),
            signal=str(signal),
            score=score,
            confidence=float(kronos.get("confidence") or 0.65),
            rationale=str(kronos.get("rationale") or kronos.get("reason") or "Kronos forecast evidence"),
            risks=risks,
            evidence=evidence,
            artifact_paths=list(kronos.get("artifact_paths") or []),
        )

    @staticmethod
    def _optional_float(value) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _first_float(source: dict, keys: tuple[str, ...]) -> float | None:
        for key in keys:
            if key in source:
                value = SimulationEngine._optional_float(source.get(key))
                if value is not None:
                    return value
        return None

    @staticmethod
    def _technical_reasoning_signal(
        candidate: dict,
        validation: dict,
        tech_detail: dict,
        news_list: list[dict],
    ) -> ReasoningSignal:
        change_pct = float(validation.get("change_pct") or 0)
        score = 50.0
        signal = "hold"
        risks: list[str] = []
        if change_pct <= -0.08:
            signal = "sell"
            score = 35.0
            risks.append("review_drawdown")
        elif change_pct >= 0.03 and candidate.get("signal") == "buy":
            signal = "buy"
            score = 66.0
        elif candidate.get("signal") == "buy":
            signal = "hold"
            score = 58.0

        ma = tech_detail.get("ma", {}) if tech_detail else {}
        if ma and ma.get("ma5", 0) > ma.get("ma20", 0):
            score += 5
            if signal == "hold":
                signal = "buy"
        elif ma and ma.get("ma5", 0) < ma.get("ma20", 0):
            score -= 5
            risks.append("weak_momentum")

        negative_news = sum(1 for item in news_list if item.get("sentiment") == "negative")
        positive_news = sum(1 for item in news_list if item.get("sentiment") == "positive")
        if negative_news > positive_news:
            score -= 5
            risks.append("negative_news")
        elif positive_news > negative_news:
            score += 3

        return ReasoningSignal(
            provider="technical",
            symbol=str(candidate.get("symbol") or ""),
            name=str(candidate.get("name") or candidate.get("symbol") or ""),
            signal=signal,
            score=max(0.0, min(score, 100.0)),
            confidence=0.6,
            rationale=(
                f"Daily technical/news overlay: price change {change_pct:.2%}, "
                f"news balance +{positive_news}/-{negative_news}."
            ),
            risks=risks,
            evidence={"technical": tech_detail, "change_pct": change_pct},
        )

    @staticmethod
    def _rules_reasoning_signal(candidate: dict, rule_checks: list[dict]) -> ReasoningSignal | None:
        if not rule_checks:
            return None
        failed = [item for item in rule_checks if not item.get("passed")]
        if failed:
            return ReasoningSignal(
                provider="rules",
                symbol=str(candidate.get("symbol") or ""),
                name=str(candidate.get("name") or candidate.get("symbol") or ""),
                signal="sell",
                score=30.0,
                confidence=0.8,
                rationale="Trading rules reported blocking issues.",
                risks=["blocking_rules"],
                evidence={"failed_rules": failed},
            )
        return ReasoningSignal(
            provider="rules",
            symbol=str(candidate.get("symbol") or ""),
            name=str(candidate.get("name") or candidate.get("symbol") or ""),
            signal="hold",
            score=58.0,
            confidence=0.5,
            rationale="Trading rules did not report blocking issues.",
            evidence={"passed_rules": rule_checks},
        )

    def _execute_quant_decision(
        self,
        candidate: dict,
        decision: QuantDecision,
    ) -> tuple[str, str]:
        if self._started_once and not self.is_running():
            return "skipped", "模拟交易引擎已停止，跳过量化执行"
        if not decision.executable:
            return "skipped", f"量化策略保持观察 | {decision.rationale}"

        result = SimpleNamespace(
            signal=decision.signal,
            score=decision.score,
            reason=decision.rationale,
        )
        symbol = candidate.get("symbol", "")
        name = candidate.get("name", symbol)
        if decision.action == "buy":
            executed, reason = self._execute_buy(
                symbol,
                name,
                result,
                allocation_pct=decision.allocation_pct,
            )
            return (
                "executed" if executed else "skipped",
                f"量化买入{'执行' if executed else '未执行'}：{reason} | {decision.rationale}",
            )
        if decision.action == "sell":
            executed, reason = self._execute_sell(symbol, name, result)
            return (
                "executed" if executed else "skipped",
                f"量化卖出{'执行' if executed else '未执行'}：{reason} | {decision.rationale}",
            )
        return "skipped", f"量化策略保持观察 | {decision.rationale}"

    @staticmethod
    def _optimization_action(
        candidate: dict,
        validation: dict,
        position: dict | None,
        rule_checks: list[dict],
    ) -> str:
        change_pct = float(validation.get("change_pct") or 0)
        signal = candidate.get("signal", "hold")
        failed_rules = [r for r in rule_checks if not r.get("passed")]
        if signal == "buy" and change_pct <= -0.08:
            return "review_drawdown"
        if signal == "buy" and failed_rules:
            return "pause_buying"
        if signal == "sell" and position:
            return "consider_reduce"
        if signal == "buy" and not position and change_pct >= 0.03:
            return "watch_pullback"
        return "keep_plan"

    @staticmethod
    def _optimization_rationale(
        candidate: dict,
        validation: dict,
        position: dict | None,
        news_list: list[dict],
        tech_detail: dict,
        rule_checks: list[dict],
        action: str,
    ) -> str:
        change_pct = float(validation.get("change_pct") or 0)
        signal = candidate.get("signal", "hold")
        score = candidate.get("score", 0)
        parts = [
            f"Weekly quant baseline was {signal} with score {score}.",
            f"Price moved {change_pct:.2%} versus the baseline.",
        ]
        if position:
            parts.append(
                "The simulated account already holds "
                f"{position.get('volume', 0)} shares at avg cost {position.get('avg_cost', 0)}."
            )
        else:
            parts.append("The simulated account does not currently hold this symbol.")

        if news_list:
            sentiment_counts = {
                "positive": sum(1 for n in news_list if n.get("sentiment") == "positive"),
                "negative": sum(1 for n in news_list if n.get("sentiment") == "negative"),
                "neutral": sum(1 for n in news_list if n.get("sentiment") == "neutral"),
            }
            parts.append(f"Same-day news sentiment counts: {sentiment_counts}.")
            latest_title = news_list[0].get("title")
            if latest_title:
                parts.append(f"Latest news: {latest_title}.")
        else:
            parts.append("No same-day news context was available.")

        if tech_detail:
            parts.append(f"Technical context keys: {', '.join(sorted(tech_detail.keys()))}.")
        else:
            parts.append("No technical context was available.")

        failed_rules = [r.get("rule_title") or r.get("rule_id") for r in rule_checks if not r.get("passed")]
        if failed_rules:
            parts.append(f"Failed rules: {', '.join(str(item) for item in failed_rules[:3])}.")
        elif rule_checks:
            parts.append("Rule checks did not flag blocking issues.")
        else:
            parts.append("No rule-check context was available.")

        parts.append(f"Optimization action: {action}.")
        return " ".join(parts)

    def _build_daily_optimization_report(
        self,
        report_date: str,
        week_id: str,
        weekly_report: dict,
        optimizations: list[dict],
    ) -> str:
        rows = []
        rationale_sections = []
        for item in optimizations:
            rows.append(
                "| {symbol} | {signal} | {weekly_score:.0f} | {quant_score:.0f} | {base:.2f} | {current:.2f} | {change:.2%} | {action} | {execution} |".format(
                    symbol=item.get("symbol", ""),
                    signal=item.get("weekly_signal", "hold"),
                    weekly_score=float(item.get("weekly_score") or 0),
                    quant_score=float(item.get("quant_score") or 0),
                    base=float(item.get("baseline_price") or 0),
                    current=float(item.get("current_price") or 0),
                    change=float(item.get("change_pct") or 0),
                    action=item.get("action", "keep_plan"),
                    execution=item.get("execution", {}).get("action_taken", "skipped"),
                )
            )
            rationale_sections.append(
                "### {symbol} {name}\n\n- Action: {action}\n- Risk flags: {risks}\n- Execution: {execution}\n\n{rationale}".format(
                    symbol=item.get("symbol", ""),
                    name=item.get("name", ""),
                    action=item.get("action", "hold"),
                    risks=", ".join(item.get("risk_flags") or []) or "none",
                    execution=item.get("execution", {}).get("action_reason", ""),
                    rationale=item.get("rationale", ""),
                )
            )

        table = "\n".join(rows) if rows else "| - | - | - | - | - | - | - | - | - |"
        rationale = "\n\n".join(rationale_sections) if rationale_sections else "No candidates."
        return f"""# Daily Quant Optimization

- Date: {report_date}
- Week: {week_id}
- Source weekly report: {weekly_report.get("report_date", "")} / {weekly_report.get("report_id", "")}
- Decision model: multi-provider reasoning -> quant policy -> simulated execution

| Symbol | Weekly Signal | Weekly Score | Quant Score | Baseline Price | Current Price | Change | Quant Action | Execution |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
{table}

## Quant Rationale

{rationale}
"""

    def _save_optimization_artifacts(
        self,
        report_date: str,
        markdown: str,
        payload: dict,
    ) -> dict:
        try:
            output_dir = self.review_output_dir / report_date
            output_dir.mkdir(parents=True, exist_ok=True)
            markdown_path = output_dir / "report.md"
            json_path = output_dir / "analysis.json"
            markdown_path.write_text(markdown, encoding="utf-8")
            json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"report_path": str(markdown_path), "analysis_path": str(json_path)}
        except Exception as exc:
            logger.error(f"Daily optimization artifact export failed: {exc}")
            return {"error": str(exc)}


    def _save_thinking_artifacts(
        self,
        report_date: str,
        review: dict,
    ) -> dict:
        try:
            output_dir = self.thinking_output_dir / report_date
            output_dir.mkdir(parents=True, exist_ok=True)
            markdown_path = output_dir / "thinking.md"
            json_path = output_dir / "thinking.json"
            markdown_path.write_text(render_thinking_markdown(review), encoding="utf-8")
            json_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
            return {"thinking_path": str(markdown_path), "thinking_json_path": str(json_path)}
        except Exception as exc:
            logger.error(f"Daily thinking artifact export failed: {exc}")
            return {"error": str(exc)}

    def _build_quant_weekly_long_term_report(
        self,
        report_date: str,
        week_id: str,
        decisions: list[dict],
    ) -> str:
        rows = []
        rationale_sections = []
        for item in decisions:
            rows.append(
                "| {symbol} | {name} | {signal} | {score:.0f} | {price:.2f} | {risks} |".format(
                    symbol=item.get("symbol", ""),
                    name=item.get("name", ""),
                    signal=item.get("signal", "hold"),
                    score=float(item.get("score") or 0),
                    price=float(item.get("price") or 0),
                    risks=", ".join(item.get("risks") or []) or "none",
                )
            )
            rationale_sections.append(
                "### {symbol} {name}\n\n{reason}".format(
                    symbol=item.get("symbol", ""),
                    name=item.get("name", ""),
                    reason=item.get("reason", ""),
                )
            )

        table = "\n".join(rows) if rows else "| - | - | - | - | - | - |"
        rationale = "\n\n".join(rationale_sections) if rationale_sections else "No candidates."
        return f"""# Quant Long-Term Plan

- Date: {report_date}
- Week: {week_id}
- Baseline model: technical screen score + momentum/news/rule risk overlay
- Execution model: daily QuantLongTermPolicy only

| Symbol | Name | Quant Signal | Quant Score | Baseline Price | Risk Flags |
| --- | --- | --- | ---: | ---: | --- |
{table}

## Quant Thesis

{rationale}
"""

    def _build_weekly_long_term_report(
        self,
        report_date: str,
        week_id: str,
        decisions: list[dict],
    ) -> str:
        """生成周度 TradingAgents 长线分析报告。"""
        rows = []
        for item in decisions:
            rows.append(
                "| {symbol} | {name} | {signal} | {score:.0f} | {price:.2f} | {action} |".format(
                    symbol=item.get("symbol", ""),
                    name=item.get("name", ""),
                    signal=item.get("signal", "hold"),
                    score=float(item.get("score") or 0),
                    price=float(item.get("price") or 0),
                    action=item.get("action_taken", "skipped"),
                )
            )
        table = "\n".join(rows) if rows else "| - | - | - | - | - | - |"
        return f"""# TradingAgents 长线周分析报告

- 日期: {report_date}
- 周期: {week_id}
- 分析策略: TradingAgents 多智能体
- 持仓倾向: 周报只作为研究基准，不直接买卖；每日由量化策略综合多源证据执行模拟操作

| 代码 | 名称 | 信号 | 评分 | 分析价 | 执行状态 |
| --- | --- | --- | ---: | ---: | --- |
{table}

## 核心结论

本报告作为本周长线模拟交易基准；后续交易日会对比 TradingAgents、Vibe-Trading/回测证据、技术面与交易准则，由量化策略统一决定是否模拟买卖。
"""

    def _build_daily_validation_report(
        self,
        report_date: str,
        week_id: str,
        weekly_report: dict,
        validations: list[dict],
    ) -> str:
        """生成每日验证报告。"""
        rows = []
        for item in validations:
            rows.append(
                "| {symbol} | {signal} | {score:.0f} | {base:.2f} | {current:.2f} | {change:.2%} | {status} |".format(
                    symbol=item.get("symbol", ""),
                    signal=item.get("signal", "hold"),
                    score=float(item.get("score") or 0),
                    base=float(item.get("baseline_price") or 0),
                    current=float(item.get("current_price") or 0),
                    change=float(item.get("change_pct") or 0),
                    status=item.get("status", "继续跟踪"),
                )
            )
        table = "\n".join(rows) if rows else "| - | - | - | - | - | - | - |"
        return f"""# Quant 长线每日验证报告

- 日期: {report_date}
- 周期: {week_id}
- 来源周报: {weekly_report.get("report_date", "")} / {weekly_report.get("report_id", "")}

| 代码 | 周度信号 | 周度评分 | 基准价 | 当前价 | 变化 | 验证结论 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
{table}

## 每日验证

该报告只验证周度量化基准是否仍然有效，不重新生成买卖观点。若出现显著反向波动或价格不可得，应在下一次周分析前复核量化条件。
"""

    @staticmethod
    def _validation_status(candidate: dict, change_pct: float) -> str:
        signal = candidate.get("signal", "hold")
        if signal == "buy" and change_pct <= -0.08:
            return "买入结论承压，建议复核"
        if signal == "sell" and change_pct >= 0.08:
            return "卖出结论承压，建议复核"
        return "结论仍可跟踪"

    async def _run_analysis_cycle_impl(self):
        """执行一次盘中分析周期

        1. 获取推荐股票
        2. 对每只股票运行分析
        3. 记录分析日志
        """
        logger.info("开始盘中分析周期")
        self._record_system_operation(
            action_taken="executed",
            action_reason="开始盘中分析周期，正在筛选候选股票",
        )

        # 获取推荐股票
        try:
            from src.analysis.strategies.stock_picker import get_stock_recommendations
            recommendations = await get_stock_recommendations(
                "A",
                10,
                use_ai_screen=False,
                progress_callback=lambda message: self._record_system_operation(
                    action_taken="executed",
                    action_reason=message,
                ),
            )
        except Exception as e:
            logger.warning(f"获取推荐失败: {e}")
            self._record_system_operation(
                action_taken="skipped",
                action_reason=f"候选股票筛选失败：{e}",
            )
            recommendations = []

        if not recommendations:
            logger.info("无推荐股票，跳过分析")
            self._record_system_operation(
                action_taken="skipped",
                action_reason="本轮未产生推荐股票，未执行买卖操作",
            )
            return {"status": "completed", "recommendations": 0, "trades": 0}

        self._record_system_operation(
            action_taken="executed",
            action_reason=f"候选筛选完成，共 {len(recommendations)} 只，开始逐只 AI 决策",
        )

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

                    # 获取新闻（用于 AI 分析上下文和分析理由）
                    news_list = await self._fetch_news(symbol, limit=5)

                    # 将新闻作为上下文传入 AI 分析
                    news_context = None
                    if news_list:
                        news_summary = "\n".join([
                            f"- [{n.get('sentiment', 'neutral')}] {n.get('title', '')}"
                            for n in news_list[:3]
                        ])
                        news_context = {"recent_news": news_summary}

                    result = await service.analyze_stock(symbol, strategy, context=news_context)

                    # 获取技术指标详情
                    tech_detail = await self._get_technical_detail(symbol)

                    # 运行准则检查
                    rule_checks = await self._check_rules(stock, result.signal)

                    # 生成详细分析理由（包含新闻）
                    detailed_reason = self._build_detailed_reason(
                        result, tech_detail, rule_checks, stock, news_list
                    )

                    # 判断执行状态
                    if result.signal == "buy" and result.score >= 55:
                        executed, execution_reason = self._execute_buy(symbol, name, result)
                        action_taken = "executed" if executed else "skipped"
                        action_reason = (
                            f"买入执行 | 评分 {result.score} >= 55 | {detailed_reason}"
                            if executed
                            else f"买入未执行：{execution_reason} | {detailed_reason}"
                        )
                    elif result.signal == "sell" and result.score <= 45:
                        executed, execution_reason = self._execute_sell(symbol, name, result)
                        action_taken = "executed" if executed else "skipped"
                        action_reason = (
                            f"卖出执行 | 评分 {result.score} <= 45 | {detailed_reason}"
                            if executed
                            else f"卖出未执行：{execution_reason} | {detailed_reason}"
                        )
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
        trade_count = len(self._get_trades(date.today().isoformat()))
        self._record_system_operation(
            action_taken="executed",
            action_reason=(
                f"盘中分析周期完成：分析 {len(recommendations)} 只候选股，"
                f"今日累计成交 {trade_count} 笔"
            ),
        )
        logger.info("盘中分析周期完成")
        return {
            "status": "completed",
            "recommendations": len(recommendations),
            "trades": trade_count,
        }

    def _build_detailed_reason(
        self, result, tech_detail: dict, rule_checks: list, stock: dict, news_list: list = None
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

        # 3. 新闻舆情
        if news_list:
            news_highlights = []
            positive_count = sum(1 for n in news_list if n.get("sentiment") == "positive")
            negative_count = sum(1 for n in news_list if n.get("sentiment") == "negative")

            if positive_count > negative_count:
                news_highlights.append(f"舆情偏正面({positive_count}条)")
            elif negative_count > positive_count:
                news_highlights.append(f"舆情偏负面({negative_count}条)")

            # 取最新一条新闻标题
            if news_list:
                latest_title = news_list[0].get("title", "")
                if latest_title:
                    title_brief = latest_title[:30] + "..." if len(latest_title) > 30 else latest_title
                    news_highlights.append(f"最新: {title_brief}")

            if news_highlights:
                parts.append(f"舆情: {', '.join(news_highlights)}")

        # 4. 准则检查结果
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

    def _execute_buy(
        self,
        symbol: str,
        name: str,
        result,
        allocation_pct: float | None = None,
    ) -> tuple[bool, str]:
        """执行买入"""
        # 检查是否已持有
        positions = self._get_positions()
        if any(p["symbol"] == symbol for p in positions):
            logger.info(f"已持有 {symbol}，跳过买入")
            return False, "当前账户已持有该股票"

        account = self._get_account()
        balance = account["balance"]
        # 动态分配资金：长线模式可传入更保守的单票资金上限。
        if allocation_pct is not None:
            alloc_pct = allocation_pct
        else:
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
            return False, "可用资金不足"

        # 获取真实价格
        price = self._get_price(symbol)
        if price <= 0:
            logger.warning(f"无法获取价格，跳过买入: {symbol}")
            return False, "无法获取价格"

        volume = int(buy_amount / price / 100) * 100  # 取整到 100 股
        if volume <= 0:
            return False, "可用资金不足以买入 100 股"

        actual_amount = price * volume
        commission = actual_amount * 0.0003

        self._update_account_balance("BUY", actual_amount, commission)
        self._update_position(symbol, name, "BUY", price, volume)
        self._record_trade(symbol, name, "BUY", price, volume, actual_amount, commission,
                           strategy=result.signal, signal_score=result.score, signal_reason=result.reason)
        logger.info(f"模拟买入: {symbol} {volume}股 @ {price}")
        return True, f"成交 {volume} 股，价格 {price}"

    def _execute_sell(self, symbol: str, name: str, result) -> tuple[bool, str]:
        """执行卖出"""
        positions = self._get_positions()
        pos = next((p for p in positions if p["symbol"] == symbol), None)
        if not pos:
            return False, "当前账户没有该股票持仓"

        # 获取真实价格，回退到持仓成本价
        price = self._get_price(symbol)
        if price <= 0:
            price = pos.get("avg_cost", 0)
        if price <= 0:
            logger.warning(f"无法获取价格，跳过卖出: {symbol}")
            return False, "无法获取价格"

        volume = pos["volume"]
        actual_amount = price * volume
        commission = actual_amount * 0.0003

        self._update_account_balance("SELL", actual_amount, commission)
        self._update_position(symbol, name, "SELL", price, volume)
        self._record_trade(symbol, name, "SELL", price, volume, actual_amount, commission,
                           strategy=result.signal, signal_score=result.score, signal_reason=result.reason)
        logger.info(f"模拟卖出: {symbol} {volume}股 @ {price}")
        return True, f"成交 {volume} 股，价格 {price}"
