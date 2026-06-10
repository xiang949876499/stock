"""数据库"""

from pathlib import Path
import sqlite3

from src.infra.logger import get_logger

logger = get_logger("database")


class Database:
    """数据库"""

    def __init__(self, db_path: str = "./data/stock_hub.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None

    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        logger.info(f"连接数据库: {self.db_path}")

    def disconnect(self):
        """断开数据库"""
        if self.conn:
            self.conn.close()
            logger.info("断开数据库")

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行 SQL"""
        if not self.conn:
            self.connect()
        return self.conn.execute(sql, params)

    def commit(self):
        """提交事务"""
        if self.conn:
            self.conn.commit()

    def init_tables(self):
        """初始化表"""
        # 信号表
        self.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                signal_id TEXT PRIMARY KEY,
                as_of TEXT NOT NULL,
                source TEXT NOT NULL,
                status TEXT NOT NULL,
                targets TEXT NOT NULL,
                cash_weight REAL DEFAULT 0,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 审计日志表
        self.execute("""
            CREATE TABLE IF NOT EXISTS signal_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT NOT NULL,
                action TEXT NOT NULL,
                operator TEXT,
                from_status TEXT,
                to_status TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.commit()
        logger.info("初始化数据库表")

    def init_sim_tables(self):
        """初始化模拟交易表"""
        self.execute("""
            CREATE TABLE IF NOT EXISTS sim_accounts (
                account_id TEXT PRIMARY KEY,
                initial_capital REAL NOT NULL,
                balance REAL NOT NULL,
                frozen REAL DEFAULT 0,
                total_assets REAL NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.execute("""
            CREATE TABLE IF NOT EXISTS sim_positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT,
                volume INTEGER NOT NULL,
                avg_cost REAL NOT NULL,
                current_price REAL,
                market_value REAL,
                pnl REAL,
                pnl_pct REAL,
                open_date TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(account_id, symbol)
            )
        """)

        self.execute("""
            CREATE TABLE IF NOT EXISTS sim_trades (
                trade_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT,
                side TEXT NOT NULL,
                price REAL NOT NULL,
                volume INTEGER NOT NULL,
                amount REAL NOT NULL,
                commission REAL DEFAULT 0,
                strategy TEXT,
                signal_score REAL,
                signal_reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.execute("""
            CREATE TABLE IF NOT EXISTS sim_daily_reports (
                report_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                report_date TEXT NOT NULL,
                total_assets REAL,
                daily_pnl REAL,
                daily_pnl_pct REAL,
                total_pnl REAL,
                total_pnl_pct REAL,
                max_drawdown REAL,
                win_rate REAL,
                trade_count INTEGER,
                report_markdown TEXT,
                mistakes TEXT,
                strategy_adjustments TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(account_id, report_date)
            )
        """)

        self.execute("""
            CREATE TABLE IF NOT EXISTS sim_analysis_logs (
                log_id TEXT PRIMARY KEY,
                account_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                strategy TEXT,
                score REAL,
                signal TEXT,
                trend TEXT,
                reason TEXT,
                action_taken TEXT,
                action_reason TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.commit()
        logger.info("初始化模拟交易表")
