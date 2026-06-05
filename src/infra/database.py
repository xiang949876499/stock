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
