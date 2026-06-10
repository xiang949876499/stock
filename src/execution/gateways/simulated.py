"""模拟交易网关"""

import uuid
from datetime import datetime

from src.execution.gateways.base import BaseGateway, Order, Trade, Position, Account
from src.infra.database import Database
from src.infra.logger import get_logger

logger = get_logger("simulated_gateway")

ACCOUNT_ID = "sim_001"
INITIAL_CAPITAL = 1_000_000.0  # 100万
COMMISSION_RATE = 0.0003  # 万三


def get_current_price(symbol: str) -> float:
    """从 akshare 获取当前价格（使用日线最新收盘价）"""
    import akshare as ak

    # symbol format: 600519.SH -> 600519, 或直接 600519
    code = symbol.split(".")[0]
    try:
        # 使用日线接口，比全市场快照快得多
        df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
        if df is not None and not df.empty:
            return float(df.iloc[-1]["收盘"])
    except Exception as e:
        logger.warning(f"获取价格失败 {symbol}: {e}")
    return 0.0


class SimulatedGateway(BaseGateway):
    """模拟交易网关"""

    def __init__(self, db: Database):
        super().__init__(gateway_name="Simulated")
        self.db = db
        self.account_id = ACCOUNT_ID

    async def connect(self, config: dict) -> bool:
        """连接 - 创建模拟账户（如不存在）"""
        self.db.init_sim_tables()

        # Check if account already exists
        rows = self.db.execute(
            "SELECT account_id FROM sim_accounts WHERE account_id = ?",
            (self.account_id,),
        ).fetchall()

        if not rows:
            self.db.execute(
                """INSERT INTO sim_accounts
                   (account_id, initial_capital, balance, frozen, total_assets)
                   VALUES (?, ?, ?, 0, ?)""",
                (self.account_id, INITIAL_CAPITAL, INITIAL_CAPITAL, INITIAL_CAPITAL),
            )
            self.db.commit()
            logger.info(f"创建模拟账户: {self.account_id}, 初始资金: {INITIAL_CAPITAL}")

        logger.info("模拟网关连接成功")
        return True

    async def disconnect(self):
        """断开 - 无操作"""
        logger.info("模拟网关断开")

    async def send_order(self, order: Order) -> str:
        """发送委托 - 模拟即时成交"""
        trade_id = f"SIM-{uuid.uuid4().hex[:8]}"
        amount = order.price * order.volume
        commission = amount * COMMISSION_RATE

        if order.offset == "OPEN":
            # 买入开仓：检查余额，扣款，建仓
            account = await self.get_account()
            if account.balance < amount + commission:
                raise ValueError(
                    f"资金不足: 需要 {amount + commission:.2f}, 可用 {account.balance:.2f}"
                )

            # 扣除余额
            self.db.execute(
                "UPDATE sim_accounts SET balance = balance - ?, total_assets = total_assets - ? WHERE account_id = ?",
                (amount + commission, commission, self.account_id),
            )

            # Upsert 持仓
            existing = self.db.execute(
                "SELECT volume, avg_cost FROM sim_positions WHERE account_id = ? AND symbol = ?",
                (self.account_id, order.vt_symbol),
            ).fetchall()

            if existing:
                old_vol = existing[0]["volume"]
                old_cost = existing[0]["avg_cost"]
                new_vol = old_vol + order.volume
                new_avg = (old_cost * old_vol + order.price * order.volume) / new_vol
                self.db.execute(
                    "UPDATE sim_positions SET volume = ?, avg_cost = ?, updated_at = ? WHERE account_id = ? AND symbol = ?",
                    (new_vol, new_avg, datetime.now().isoformat(), self.account_id, order.vt_symbol),
                )
            else:
                self.db.execute(
                    """INSERT INTO sim_positions
                       (account_id, symbol, volume, avg_cost, current_price, market_value, pnl, pnl_pct, open_date, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?)""",
                    (
                        self.account_id,
                        order.vt_symbol,
                        order.volume,
                        order.price,
                        order.price,
                        amount,
                        datetime.now().strftime("%Y-%m-%d"),
                        datetime.now().isoformat(),
                    ),
                )

            side = "BUY"
            logger.info(f"买入成交: {order.vt_symbol} x{order.volume} @ {order.price}")

        elif order.offset == "CLOSE":
            # 卖出平仓：检查持仓，加回余额
            existing = self.db.execute(
                "SELECT volume, avg_cost FROM sim_positions WHERE account_id = ? AND symbol = ?",
                (self.account_id, order.vt_symbol),
            ).fetchall()

            if not existing or existing[0]["volume"] < order.volume:
                held = existing[0]["volume"] if existing else 0
                raise ValueError(
                    f"持仓不足: {order.vt_symbol} 持有 {held}, 卖出 {order.volume}"
                )

            old_vol = existing[0]["volume"]
            new_vol = old_vol - order.volume

            if new_vol == 0:
                self.db.execute(
                    "DELETE FROM sim_positions WHERE account_id = ? AND symbol = ?",
                    (self.account_id, order.vt_symbol),
                )
            else:
                self.db.execute(
                    "UPDATE sim_positions SET volume = ?, updated_at = ? WHERE account_id = ? AND symbol = ?",
                    (new_vol, datetime.now().isoformat(), self.account_id, order.vt_symbol),
                )

            # 加回余额（卖出所得 - 手续费）
            net_proceeds = amount - commission
            self.db.execute(
                "UPDATE sim_accounts SET balance = balance + ?, total_assets = total_assets - ? WHERE account_id = ?",
                (net_proceeds, commission, self.account_id),
            )

            side = "SELL"
            logger.info(f"卖出成交: {order.vt_symbol} x{order.volume} @ {order.price}")

        else:
            raise ValueError(f"未知 offset: {order.offset}")

        # 记录成交
        self.db.execute(
            """INSERT INTO sim_trades
               (trade_id, account_id, symbol, side, price, volume, amount, commission, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                trade_id,
                self.account_id,
                order.vt_symbol,
                side,
                order.price,
                order.volume,
                amount,
                commission,
                datetime.now().isoformat(),
            ),
        )
        self.db.commit()

        return trade_id

    async def cancel_order(self, vt_orderid: str):
        """撤销委托 - 模拟网关直接成交，无法撤销"""
        logger.warning(f"模拟网关无法撤销委托: {vt_orderid}（已直接成交）")

    async def get_positions(self) -> list[Position]:
        """获取持仓"""
        rows = self.db.execute(
            "SELECT symbol, volume, avg_cost, current_price, pnl FROM sim_positions WHERE account_id = ?",
            (self.account_id,),
        ).fetchall()

        positions = []
        for row in rows:
            positions.append(
                Position(
                    vt_symbol=row["symbol"],
                    direction="LONG",
                    volume=row["volume"],
                    price=row["avg_cost"],
                    pnl=row["pnl"] or 0.0,
                )
            )
        return positions

    async def get_account(self) -> Account:
        """获取账户"""
        rows = self.db.execute(
            "SELECT account_id, balance, frozen FROM sim_accounts WHERE account_id = ?",
            (self.account_id,),
        ).fetchall()

        if not rows:
            raise ValueError(f"账户不存在: {self.account_id}")

        row = rows[0]
        return Account(
            account_id=row["account_id"],
            balance=row["balance"],
            available=row["balance"] - (row["frozen"] or 0),
            frozen=row["frozen"] or 0,
        )

    async def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        return get_current_price(symbol)
