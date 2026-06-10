"""SimulationEngine - 模拟交易核心引擎

协调 analysis -> signal -> execution -> recording 流程。
"""

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
        self._init_account()

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
    ):
        """写入分析日志"""
        log_id = f"L-{uuid.uuid4().hex[:12]}"
        self.db.execute(
            "INSERT INTO sim_analysis_logs "
            "(log_id, account_id, symbol, strategy, score, signal, trend, reason, action_taken, action_reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (log_id, self.account_id, symbol, strategy, score, signal, trend, reason, action_taken, action_reason),
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
