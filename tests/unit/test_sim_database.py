"""模拟交易数据库测试"""

import pytest
import tempfile
import os
from src.infra.database import Database


@pytest.fixture
def db():
    """创建临时数据库"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    db = Database(db_path)
    db.connect()
    db.init_sim_tables()
    yield db
    db.disconnect()
    os.unlink(db_path)


def test_init_sim_tables(db):
    """测试模拟交易表创建"""
    cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    assert "sim_accounts" in tables
    assert "sim_positions" in tables
    assert "sim_trades" in tables
    assert "sim_daily_reports" in tables
    assert "sim_analysis_logs" in tables


def test_create_account(db):
    """测试创建模拟账户"""
    db.execute(
        "INSERT INTO sim_accounts (account_id, initial_capital, balance, total_assets) VALUES (?, ?, ?, ?)",
        ("sim_001", 1000000, 1000000, 1000000)
    )
    db.commit()
    cursor = db.execute("SELECT * FROM sim_accounts WHERE account_id = ?", ("sim_001",))
    row = cursor.fetchone()
    assert row is not None
    assert row[1] == 1000000
    assert row[2] == 1000000
