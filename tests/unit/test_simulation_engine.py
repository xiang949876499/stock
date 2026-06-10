"""SimulationEngine tests"""

import pytest
from unittest.mock import MagicMock

from src.trading.engine import SimulationEngine
from src.infra.database import Database


@pytest.fixture
def db(tmp_path):
    """Create a Database with sim tables for testing."""
    db = Database(db_path=str(tmp_path / "test_engine.db"))
    db.connect()
    db.init_sim_tables()
    return db


@pytest.fixture
def engine(db):
    """Create a SimulationEngine instance."""
    return SimulationEngine(db=db)


# ── _init_account ──────────────────────────────────────────────────


class TestInitAccount:
    def test_creates_account_with_100w(self, engine, db):
        """_init_account should create an account with 1,000,000 balance."""
        rows = db.execute(
            "SELECT * FROM sim_accounts WHERE account_id = ?", ("sim_001",)
        ).fetchall()
        assert len(rows) == 1
        row = rows[0]
        assert row["initial_capital"] == 1_000_000.0
        assert row["balance"] == 1_000_000.0
        assert row["frozen"] == 0.0
        assert row["total_assets"] == 1_000_000.0

    def test_init_account_idempotent(self, engine, db):
        """Calling _init_account twice should not overwrite existing account."""
        # Modify balance to simulate trading
        db.execute(
            "UPDATE sim_accounts SET balance = 500000 WHERE account_id = ?",
            ("sim_001",),
        )
        db.commit()

        # Re-create engine (triggers _init_account again)
        engine2 = SimulationEngine(db=db)

        rows = db.execute(
            "SELECT balance FROM sim_accounts WHERE account_id = ?", ("sim_001",)
        ).fetchall()
        assert rows[0]["balance"] == 500_000.0  # unchanged


# ── _get_account ───────────────────────────────────────────────────


class TestGetAccount:
    def test_returns_correct_data(self, engine):
        """_get_account should return a dict with correct account data."""
        account = engine._get_account()
        assert account["account_id"] == "sim_001"
        assert account["initial_capital"] == 1_000_000.0
        assert account["balance"] == 1_000_000.0
        assert account["total_assets"] == 1_000_000.0

    def test_returns_dict(self, engine):
        """_get_account should return a dict."""
        account = engine._get_account()
        assert isinstance(account, dict)


# ── _get_positions ─────────────────────────────────────────────────


class TestGetPositions:
    def test_returns_empty_list_initially(self, engine):
        """_get_positions should return empty list when no positions exist."""
        positions = engine._get_positions()
        assert positions == []

    def test_returns_positions_after_trade(self, engine, db):
        """_get_positions should return positions after a buy trade."""
        engine._update_position("600519", "贵州茅台", "BUY", 1800.0, 100)
        positions = engine._get_positions()
        assert len(positions) == 1
        assert positions[0]["symbol"] == "600519"
        assert positions[0]["volume"] == 100


# ── _record_trade ──────────────────────────────────────────────────


class TestRecordTrade:
    def test_writes_trade_to_db(self, engine, db):
        """_record_trade should insert a trade record into sim_trades."""
        engine._record_trade(
            symbol="600519",
            name="贵州茅台",
            side="BUY",
            price=1800.0,
            volume=100,
            amount=180000.0,
            commission=90.0,
            strategy="comprehensive",
            signal_score=85.0,
            signal_reason="强势上涨",
        )

        rows = db.execute(
            "SELECT * FROM sim_trades WHERE account_id = ?", ("sim_001",)
        ).fetchall()
        assert len(rows) == 1
        row = rows[0]
        assert row["symbol"] == "600519"
        assert row["name"] == "贵州茅台"
        assert row["side"] == "BUY"
        assert row["price"] == 1800.0
        assert row["volume"] == 100
        assert row["amount"] == 180000.0
        assert row["commission"] == 90.0
        assert row["strategy"] == "comprehensive"
        assert row["signal_score"] == 85.0
        assert row["signal_reason"] == "强势上涨"

    def test_trade_id_is_unique(self, engine, db):
        """Each trade should get a unique trade_id."""
        engine._record_trade("600519", "贵州茅台", "BUY", 1800.0, 100, 180000.0, 90.0)
        engine._record_trade("600519", "贵州茅台", "SELL", 1900.0, 100, 190000.0, 95.0)

        rows = db.execute(
            "SELECT trade_id FROM sim_trades WHERE account_id = ?", ("sim_001",)
        ).fetchall()
        ids = [r["trade_id"] for r in rows]
        assert len(ids) == 2
        assert ids[0] != ids[1]


# ── _update_position ───────────────────────────────────────────────


class TestUpdatePosition:
    def test_buy_new_position(self, engine, db):
        """Buying a new symbol should create a position."""
        engine._update_position("600519", "贵州茅台", "BUY", 1800.0, 100)

        rows = db.execute(
            "SELECT * FROM sim_positions WHERE account_id = ? AND symbol = ?",
            ("sim_001", "600519"),
        ).fetchall()
        assert len(rows) == 1
        row = rows[0]
        assert row["symbol"] == "600519"
        assert row["name"] == "贵州茅台"
        assert row["volume"] == 100
        assert row["avg_cost"] == 1800.0

    def test_buy_existing_position_avg_cost(self, engine, db):
        """Buying more of an existing position should use volume-weighted avg cost."""
        engine._update_position("600519", "贵州茅台", "BUY", 1800.0, 100)
        engine._update_position("600519", "贵州茅台", "BUY", 2000.0, 100)

        rows = db.execute(
            "SELECT * FROM sim_positions WHERE account_id = ? AND symbol = ?",
            ("sim_001", "600519"),
        ).fetchall()
        row = rows[0]
        assert row["volume"] == 200
        # avg_cost = (1800*100 + 2000*100) / 200 = 1900
        assert abs(row["avg_cost"] - 1900.0) < 0.01

    def test_sell_partial_position(self, engine, db):
        """Selling part of a position should reduce volume."""
        engine._update_position("600519", "贵州茅台", "BUY", 1800.0, 200)
        engine._update_position("600519", "贵州茅台", "SELL", 1900.0, 100)

        rows = db.execute(
            "SELECT * FROM sim_positions WHERE account_id = ? AND symbol = ?",
            ("sim_001", "600519"),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0]["volume"] == 100
        assert rows[0]["avg_cost"] == 1800.0  # cost unchanged on sell

    def test_sell_full_position(self, engine, db):
        """Selling all shares should remove the position."""
        engine._update_position("600519", "贵州茅台", "BUY", 1800.0, 100)
        engine._update_position("600519", "贵州茅台", "SELL", 1900.0, 100)

        rows = db.execute(
            "SELECT * FROM sim_positions WHERE account_id = ? AND symbol = ?",
            ("sim_001", "600519"),
        ).fetchall()
        assert len(rows) == 0


# ── _update_account_balance ────────────────────────────────────────


class TestUpdateAccountBalance:
    def test_buy_deducts_balance(self, engine, db):
        """BUY should deduct amount + commission from balance."""
        engine._update_account_balance("BUY", 180000.0, 90.0)

        account = engine._get_account()
        expected = 1_000_000.0 - 180000.0 - 90.0
        assert abs(account["balance"] - expected) < 0.01

    def test_sell_adds_balance(self, engine, db):
        """SELL should add amount - commission to balance."""
        # First deduct some
        engine._update_account_balance("BUY", 180000.0, 90.0)
        engine._update_account_balance("SELL", 190000.0, 95.0)

        account = engine._get_account()
        expected = 1_000_000.0 - 180000.0 - 90.0 + 190000.0 - 95.0
        assert abs(account["balance"] - expected) < 0.01


# ── _record_analysis_log ──────────────────────────────────────────


class TestRecordAnalysisLog:
    def test_writes_log_to_db(self, engine, db):
        """_record_analysis_log should insert a log into sim_analysis_logs."""
        engine._record_analysis_log(
            symbol="600519",
            strategy="comprehensive",
            score=85.0,
            signal="buy",
            trend="bullish",
            reason="强势上涨",
            action_taken="BUY",
            action_reason="信号强烈",
        )

        rows = db.execute(
            "SELECT * FROM sim_analysis_logs WHERE account_id = ?", ("sim_001",)
        ).fetchall()
        assert len(rows) == 1
        row = rows[0]
        assert row["symbol"] == "600519"
        assert row["strategy"] == "comprehensive"
        assert row["score"] == 85.0
        assert row["signal"] == "buy"
        assert row["trend"] == "bullish"


# ── _get_trades ────────────────────────────────────────────────────


class TestGetTrades:
    def test_returns_all_trades(self, engine):
        """_get_trades should return all trades when no date filter."""
        engine._record_trade("600519", "贵州茅台", "BUY", 1800.0, 100, 180000.0, 90.0)
        engine._record_trade("000001", "平安银行", "BUY", 12.0, 1000, 12000.0, 6.0)

        trades = engine._get_trades()
        assert len(trades) == 2

    def test_filters_by_date(self, engine, db):
        """_get_trades with trade_date should filter by date."""
        engine._record_trade("600519", "贵州茅台", "BUY", 1800.0, 100, 180000.0, 90.0)

        # Insert a trade with a different date
        db.execute(
            "INSERT INTO sim_trades (trade_id, account_id, symbol, side, price, volume, amount, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("T_OLD", "sim_001", "000001", "BUY", 10.0, 50, 500.0, "2020-01-01 10:00:00"),
        )
        db.commit()

        # Get today's trades only
        from datetime import date
        today = date.today().isoformat()
        trades = engine._get_trades(trade_date=today)
        # Should only get the one we inserted via _record_trade (today)
        assert all(today in t["created_at"] for t in trades)


# ── _update_total_assets ──────────────────────────────────────────


class TestUpdateTotalAssets:
    def test_calculates_total_assets(self, engine, db):
        """_update_total_assets should sum balance + position market_values."""
        # Buy some shares
        engine._update_position("600519", "贵州茅台", "BUY", 100.0, 100)
        engine._update_account_balance("BUY", 10000.0, 5.0)

        # Set current_price and market_value for the position
        db.execute(
            "UPDATE sim_positions SET current_price = 120.0, market_value = 12000.0 WHERE symbol = ?",
            ("600519",),
        )
        db.commit()

        engine._update_total_assets()

        account = engine._get_account()
        expected_balance = 1_000_000.0 - 10000.0 - 5.0
        expected_total = expected_balance + 12000.0
        assert abs(account["total_assets"] - expected_total) < 0.01


# ── start / stop / is_running ─────────────────────────────────────


class TestStartStop:
    def test_initial_state_not_running(self, engine):
        """Engine should not be running initially."""
        assert engine.is_running() is False

    def test_start_sets_running(self, engine):
        """start() should set _running to True."""
        engine.start()
        assert engine.is_running() is True

    def test_stop_clears_running(self, engine):
        """stop() should set _running to False."""
        engine.start()
        engine.stop()
        assert engine.is_running() is False

    def test_start_stop_multiple_times(self, engine):
        """start/stop should be idempotent."""
        engine.start()
        engine.start()
        assert engine.is_running() is True
        engine.stop()
        engine.stop()
        assert engine.is_running() is False


# ── get_status ─────────────────────────────────────────────────────


class TestGetStatus:
    def test_returns_status_dict(self, engine):
        """get_status should return a dict with running, account, positions."""
        status = engine.get_status()
        assert "running" in status
        assert "account" in status
        assert "positions" in status
        assert status["running"] is False
        assert status["account"]["account_id"] == "sim_001"
        assert status["positions"] == []

    def test_status_reflects_running_state(self, engine):
        """get_status should reflect current running state."""
        engine.start()
        status = engine.get_status()
        assert status["running"] is True
