"""SimulationEngine tests"""

import asyncio
import json
from datetime import date

import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from src.trading.engine import SimulationEngine
from src.infra.database import Database
from src.trading.quant_policy import QuantDecision


@pytest.fixture
def db(tmp_path):
    """Create a Database with sim tables for testing."""
    db = Database(db_path=str(tmp_path / "test_engine.db"))
    db.connect()
    db.init_sim_tables()
    return db


@pytest.fixture
def engine(db, tmp_path):
    """Create a SimulationEngine instance."""
    engine = SimulationEngine(db=db)
    engine.review_output_dir = tmp_path / "reviews"
    engine.thinking_output_dir = tmp_path / "thinking"
    return engine


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
        SimulationEngine(db=db)

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


class TestTradeExecutionResult:
    def test_buy_reports_missing_price_instead_of_claiming_execution(
        self, engine, monkeypatch
    ):
        """A buy signal is not a trade when no executable price is available."""
        result = SimpleNamespace(signal="buy", score=80, reason="test")
        monkeypatch.setattr(engine, "_get_price", lambda symbol: 0.0)

        executed, reason = engine._execute_buy("600519", "贵州茅台", result)

        assert executed is False
        assert "无法获取价格" in reason
        assert engine._get_trades() == []


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

    def test_start_sets_running_and_records_operation(self, engine, db):
        """start() should set _running and leave a visible operation log."""
        engine.start()
        assert engine.is_running() is True
        row = db.execute(
            "SELECT * FROM sim_analysis_logs WHERE account_id = ?",
            ("sim_001",),
        ).fetchone()
        assert row["symbol"] == "SYSTEM"
        assert row["action_taken"] == "executed"
        assert "引擎已启动" in row["action_reason"]

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


@pytest.mark.xfail(reason="模拟分析已改成长线周分析/每日验证，旧盘中短线断言不再适用")
@pytest.mark.asyncio
async def test_analysis_cycle_records_empty_recommendation_operation(
    engine, db, monkeypatch
):
    """An empty recommendation cycle should still be visible in analysis logs."""
    from src.analysis.strategies import stock_picker

    async def fake_recommendations(market, top_n, **kwargs):
        assert market == "A"
        assert top_n == 10
        assert kwargs["use_ai_screen"] is False
        kwargs["progress_callback"]("技术快筛进度：已检查 1000/4970 只")
        return []

    monkeypatch.setattr(stock_picker, "get_stock_recommendations", fake_recommendations)

    await engine.run_analysis_cycle()

    rows = db.execute(
        "SELECT * FROM sim_analysis_logs WHERE account_id = ? ORDER BY rowid",
        ("sim_001",),
    ).fetchall()
    assert len(rows) == 3
    assert rows[0]["symbol"] == "SYSTEM"
    assert "开始盘中分析周期" in rows[0]["action_reason"]
    assert "已检查 1000/4970" in rows[1]["action_reason"]
    assert rows[2]["action_taken"] == "skipped"
    assert "未产生推荐股票" in rows[2]["action_reason"]


@pytest.mark.asyncio
async def test_short_term_kline_monitor_buys_bullish_kline_candidate(
    engine, db, monkeypatch
):
    from src.analysis.strategies import stock_picker

    async def fake_recommendations(market, top_n, **kwargs):
        assert market == "A"
        assert top_n == 10
        return [{"symbol": "600519", "name": "Kweichow Moutai", "market": "A", "score": 72}]

    monkeypatch.setattr(stock_picker, "get_stock_recommendations", fake_recommendations)
    monkeypatch.setattr(engine, "_get_price", lambda symbol: 100.0)
    monkeypatch.setattr(engine, "_fetch_news", AsyncMock(return_value=[]))
    monkeypatch.setattr(
        engine,
        "_get_technical_detail",
        AsyncMock(
            return_value={
                "ma": {"ma5": 105, "ma10": 103, "ma20": 100},
                "macd": {"macd": 1.2, "macd_signal": 0.8},
                "rsi": {"rsi_6": 58},
                "volume": {"volume_ratio": 1.4},
            }
        ),
    )
    monkeypatch.setattr(engine, "_check_rules", AsyncMock(return_value=[]))

    result = await engine.run_analysis_cycle()

    assert result["mode"] == "short_term_kline"
    assert result["recommendations"] == 1
    trade = engine._get_trades()[0]
    assert trade["symbol"] == "600519"
    assert trade["side"] == "BUY"
    log = db.execute(
        "SELECT * FROM sim_analysis_logs WHERE account_id = ? AND symbol = ?",
        ("sim_001", "600519"),
    ).fetchone()
    assert log["strategy"] == "short_term_kline"
    assert log["signal"] == "buy"


@pytest.mark.asyncio
async def test_analysis_cycle_rejects_overlapping_run(engine, monkeypatch):
    """Manual and scheduled analysis must not run at the same time."""
    started = asyncio.Event()
    release = asyncio.Event()

    async def slow_cycle(*args, **kwargs):
        started.set()
        await release.wait()
        return {"status": "completed"}

    monkeypatch.setattr(engine, "run_short_term_kline_monitor", slow_cycle)

    first = asyncio.create_task(engine.run_analysis_cycle())
    await started.wait()
    second_result = await engine.run_analysis_cycle()
    release.set()
    await first

    assert second_result["status"] == "skipped"
    assert "已有分析周期" in second_result["message"]


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


@pytest.mark.asyncio
async def test_long_term_cycle_runs_weekly_then_daily_decision_when_week_has_no_report(
    engine, db, monkeypatch
):
    """First analysis of a week should create a quant baseline, then make a daily decision."""
    from src.analysis import service as analysis_service
    from src.analysis.strategies import stock_picker

    tradingagents_calls = []

    async def fake_recommendations(market, top_n, **kwargs):
        assert market == "A"
        assert top_n == 5
        return [{"symbol": "600519", "name": "Kweichow Moutai", "market": "A", "score": 91}]

    async def fake_analyze(self, symbol, strategy_name, context=None):
        tradingagents_calls.append(
            {
                "symbol": symbol,
                "strategy_name": strategy_name,
                "context": context,
            }
        )
        raise AssertionError("long-term simulation plan should not call TradingAgents")

    monkeypatch.setattr(stock_picker, "get_stock_recommendations", fake_recommendations)
    monkeypatch.setattr(analysis_service.AnalysisService, "analyze_stock", fake_analyze)
    monkeypatch.setattr(engine, "_fetch_news", AsyncMock(return_value=[]))
    monkeypatch.setattr(engine, "_get_technical_detail", AsyncMock(return_value={}))
    monkeypatch.setattr(engine, "_check_rules", AsyncMock(return_value=[]))
    monkeypatch.setattr(engine, "_get_price", lambda symbol: 100.0)

    await engine.run_weekly_quant_analysis(date(2026, 6, 16))
    result = await engine.run_daily_long_term_validation(date(2026, 6, 16))

    assert result["mode"] == "daily_optimization"
    assert result["report_type"] == "daily_optimization"
    assert tradingagents_calls == []

    weekly_report = db.execute(
        """
        SELECT * FROM sim_long_term_reports
        WHERE account_id = ? AND report_date = ? AND report_type = ?
        """,
        ("sim_001", "2026-06-16", "weekly_analysis"),
    ).fetchone()
    assert weekly_report is not None
    assert weekly_report["week_id"] == "2026-W25"
    assert "Quant Long-Term Plan" in weekly_report["report_markdown"]
    assert "TradingAgents" not in weekly_report["report_markdown"]
    assert "600519" in weekly_report["report_markdown"]
    candidates = json.loads(weekly_report["candidates_snapshot"])
    assert candidates[0]["provider"] == "quant_screen"
    assert candidates[0]["signal"] == "buy"
    assert candidates[0]["score"] == 91

    optimization_report = db.execute(
        """
        SELECT * FROM sim_long_term_reports
        WHERE account_id = ? AND report_date = ? AND report_type = ?
        """,
        ("sim_001", "2026-06-16", "daily_optimization"),
    ).fetchone()
    assert optimization_report is not None
    assert "Daily Quant Optimization" in optimization_report["report_markdown"]
    assert engine._get_trades()[0]["side"] == "BUY"

    log = db.execute(
        "SELECT * FROM sim_analysis_logs WHERE account_id = ? AND symbol = ?",
        ("sim_001", "600519"),
    ).fetchone()
    assert log["strategy"] == "quant_long_term_baseline"


@pytest.mark.asyncio
async def test_long_term_cycle_validates_existing_weekly_report_daily(
    engine, db, monkeypatch, tmp_path
):
    """After a weekly report exists, later runs in the same week validate it daily."""
    engine.review_output_dir = tmp_path / "reviews"
    engine.thinking_output_dir = tmp_path / "thinking"
    engine._record_long_term_report(
        report_date="2026-06-15",
        report_type="weekly_analysis",
        week_id="2026-W25",
        report_markdown="# Weekly TradingAgents",
        candidates_snapshot=[
            {"symbol": "600519", "signal": "buy", "score": 82, "price": 100.0}
        ],
    )
    engine._update_position("600519", "Kweichow Moutai", "BUY", 100.0, 100)
    monkeypatch.setattr(engine, "_get_price", lambda symbol: 108.0)
    monkeypatch.setattr(engine, "_fetch_news", AsyncMock(return_value=[]))
    monkeypatch.setattr(engine, "_get_technical_detail", AsyncMock(return_value={}))
    monkeypatch.setattr(engine, "_check_rules", AsyncMock(return_value=[]))

    result = await engine.run_daily_long_term_validation(date(2026, 6, 16))

    assert result["mode"] == "daily_optimization"
    assert result["report_type"] == "daily_optimization"
    report = db.execute(
        """
        SELECT * FROM sim_long_term_reports
        WHERE account_id = ? AND report_date = ? AND report_type = ?
        """,
        ("sim_001", "2026-06-16", "daily_validation"),
    ).fetchone()
    assert report["report_type"] == "daily_validation"


@pytest.mark.asyncio
async def test_weekly_tradingagents_transient_connection_error_degrades_to_hold(
    engine, db, monkeypatch
):
    """Transient upstream disconnects should not poison the weekly baseline as error."""
    from http.client import RemoteDisconnected

    from src.analysis import service as analysis_service
    from src.analysis.strategies import stock_picker

    async def fake_recommendations(market, top_n, **kwargs):
        return [{"symbol": "002768", "name": "Test Stock", "market": "A", "score": 77}]

    async def fail_with_disconnect(self, symbol, strategy_name, context=None):
        raise ConnectionError("Connection aborted.", RemoteDisconnected("Remote end closed connection without response"))

    monkeypatch.setattr(stock_picker, "get_stock_recommendations", fake_recommendations)
    monkeypatch.setattr(analysis_service.AnalysisService, "analyze_stock", fail_with_disconnect)
    monkeypatch.setattr(engine, "_get_price", lambda symbol: 12.3)

    result = await engine.run_weekly_tradingagents_analysis(date(2026, 6, 18))

    assert result["status"] == "completed"
    report = db.execute(
        """
        SELECT * FROM sim_long_term_reports
        WHERE account_id = ? AND report_date = ? AND report_type = ?
        """,
        ("sim_001", "2026-06-18", "weekly_analysis"),
    ).fetchone()
    candidates = json.loads(report["candidates_snapshot"])
    assert candidates[0]["signal"] == "hold"
    assert candidates[0]["score"] == 50
    assert candidates[0]["action_taken"] == "skipped"
    assert "外部连接中断" in candidates[0]["action_reason"]

    log = db.execute(
        """
        SELECT * FROM sim_analysis_logs
        WHERE account_id = ? AND symbol = ?
        """,
        ("sim_001", "002768"),
    ).fetchone()
    assert log["signal"] == "hold"
    assert "外部连接中断" in log["action_reason"]
    assert "002768" in report["report_markdown"]


@pytest.mark.asyncio
async def test_daily_long_term_validation_creates_optimization_report(
    engine, db, monkeypatch, tmp_path
):
    """Daily validation should also optimize the plan and archive artifacts."""
    engine.review_output_dir = tmp_path / "reviews"
    engine._record_long_term_report(
        report_date="2026-06-15",
        report_type="weekly_analysis",
        week_id="2026-W25",
        report_markdown="# Weekly TradingAgents",
        candidates_snapshot=[
            {
                "symbol": "600519",
                "name": "Kweichow Moutai",
                "signal": "buy",
                "score": 82,
                "price": 100.0,
                "reason": "Weekly baseline expects strength",
            }
        ],
    )
    engine._update_position("600519", "Kweichow Moutai", "BUY", 100.0, 100)
    monkeypatch.setattr(engine, "_get_price", lambda symbol: 91.0)
    monkeypatch.setattr(
        engine,
        "_fetch_news",
        AsyncMock(
            return_value=[
                {
                    "title": "Demand outlook softened",
                    "summary": "Channel checks turned cautious",
                    "sentiment": "negative",
                }
            ]
        ),
    )
    monkeypatch.setattr(
        engine,
        "_get_technical_detail",
        AsyncMock(return_value={"ma": {"ma5": 91, "ma20": 100}}),
    )
    monkeypatch.setattr(engine, "_check_rules", AsyncMock(return_value=[]))

    result = await engine.run_daily_long_term_validation(date(2026, 6, 16))

    assert result["mode"] == "daily_optimization"
    assert result["report_type"] == "daily_optimization"
    assert result["optimized"] == 1
    assert result["thinking_artifacts"]["thinking_path"].endswith("thinking.md")

    validation = db.execute(
        """
        SELECT * FROM sim_long_term_reports
        WHERE account_id = ? AND report_date = ? AND report_type = ?
        """,
        ("sim_001", "2026-06-16", "daily_validation"),
    ).fetchone()
    assert validation is not None

    report = db.execute(
        """
        SELECT * FROM sim_long_term_reports
        WHERE account_id = ? AND report_date = ? AND report_type = ?
        """,
        ("sim_001", "2026-06-16", "daily_optimization"),
    ).fetchone()
    assert report is not None
    assert "Daily Quant Optimization" in report["report_markdown"]
    assert "600519" in report["report_markdown"]
    assert "review_drawdown" in report["report_markdown"]
    assert "sell" in report["report_markdown"]

    report_path = tmp_path / "reviews" / "2026-06-16" / "report.md"
    analysis_path = tmp_path / "reviews" / "2026-06-16" / "analysis.json"
    assert report_path.exists()
    assert analysis_path.exists()
    assert "Daily Quant Optimization" in report_path.read_text(encoding="utf-8")
    payload = json.loads(analysis_path.read_text(encoding="utf-8"))
    assert payload["optimizations"][0]["action"] == "sell"
    assert "review_drawdown" in payload["optimizations"][0]["risk_flags"]

    thinking_path = tmp_path / "thinking" / "2026-06-16" / "thinking.md"
    thinking_json_path = tmp_path / "thinking" / "2026-06-16" / "thinking.json"
    assert thinking_path.exists()
    assert thinking_json_path.exists()
    thinking_payload = json.loads(thinking_json_path.read_text(encoding="utf-8"))
    assert thinking_payload["report_date"] == "2026-06-16"
    assert thinking_payload["entries"][0]["symbol"] == "600519"
    assert thinking_payload["entries"][0]["operation_judgement"] == "correct"


@pytest.mark.asyncio
async def test_daily_quant_policy_blocks_tradingagents_buy_when_vibe_is_negative(
    engine, db, monkeypatch, tmp_path
):
    """A Vibe-Trading negative backtest should block a bullish weekly thesis."""
    engine.review_output_dir = tmp_path / "reviews"
    engine._record_long_term_report(
        report_date="2026-06-15",
        report_type="weekly_analysis",
        week_id="2026-W25",
        report_markdown="# Weekly TradingAgents",
        candidates_snapshot=[
            {
                "symbol": "600519",
                "name": "Kweichow Moutai",
                "signal": "buy",
                "score": 86,
                "price": 100.0,
                "reason": "TradingAgents is bullish",
                "vibe_trading": {
                    "signal": "sell",
                    "score": 24,
                    "confidence": 0.9,
                    "rationale": "Shadow backtest is negative",
                    "backtest": {"sharpe": -0.4, "max_drawdown": -0.18},
                },
            }
        ],
    )
    monkeypatch.setattr(engine, "_get_price", lambda symbol: 101.0)
    monkeypatch.setattr(engine, "_fetch_news", AsyncMock(return_value=[]))
    monkeypatch.setattr(engine, "_get_technical_detail", AsyncMock(return_value={}))
    monkeypatch.setattr(engine, "_check_rules", AsyncMock(return_value=[]))

    result = await engine.run_daily_long_term_validation(date(2026, 6, 16))

    assert result["mode"] == "daily_optimization"
    assert engine._get_positions() == []
    assert engine._get_trades() == []

    payload = json.loads(
        (tmp_path / "reviews" / "2026-06-16" / "analysis.json").read_text(
            encoding="utf-8"
        )
    )
    row = payload["optimizations"][0]
    assert row["action"] == "hold"
    assert "negative_backtest" in row["risk_flags"]
    assert row["provider_breakdown"]["vibe_trading"]["signal"] == "sell"


@pytest.mark.asyncio
async def test_daily_quant_policy_uses_kronos_prediction_as_simulation_evidence(
    engine, db, monkeypatch, tmp_path
):
    """A bearish Kronos forecast should be preserved as evidence and block buys."""
    engine.review_output_dir = tmp_path / "reviews"
    engine._record_long_term_report(
        report_date="2026-06-15",
        report_type="weekly_analysis",
        week_id="2026-W25",
        report_markdown="# Weekly TradingAgents",
        candidates_snapshot=[
            {
                "symbol": "600519",
                "name": "Kweichow Moutai",
                "signal": "buy",
                "score": 86,
                "price": 100.0,
                "reason": "TradingAgents is bullish",
                "kronos_prediction": {
                    "forecast_return": -0.06,
                    "confidence": 0.85,
                    "horizon": "10d",
                    "rationale": "Kronos forecasts lower closes over the next window",
                },
            }
        ],
    )
    monkeypatch.setattr(engine, "_get_price", lambda symbol: 101.0)
    monkeypatch.setattr(engine, "_fetch_news", AsyncMock(return_value=[]))
    monkeypatch.setattr(engine, "_get_technical_detail", AsyncMock(return_value={}))
    monkeypatch.setattr(engine, "_check_rules", AsyncMock(return_value=[]))

    result = await engine.run_daily_long_term_validation(date(2026, 6, 16))

    assert result["mode"] == "daily_optimization"
    assert engine._get_positions() == []
    assert engine._get_trades() == []

    payload = json.loads(
        (tmp_path / "reviews" / "2026-06-16" / "analysis.json").read_text(
            encoding="utf-8"
        )
    )
    row = payload["optimizations"][0]
    assert row["action"] == "hold"
    assert "kronos_bearish_forecast" in row["risk_flags"]
    assert row["provider_breakdown"]["kronos"]["signal"] == "sell"
    assert row["provider_breakdown"]["kronos"]["evidence"]["forecast_return"] == -0.06



@pytest.mark.asyncio
async def test_daily_optimization_uses_prior_thinking_feedback(
    engine, db, monkeypatch, tmp_path
):
    """Prior daily thinking should become a provider signal in later decisions."""
    engine.review_output_dir = tmp_path / "reviews"
    engine.thinking_output_dir = tmp_path / "thinking"
    prior_dir = engine.thinking_output_dir / "2026-06-16"
    prior_dir.mkdir(parents=True)
    (prior_dir / "thinking.json").write_text(
        json.dumps(
            {
                "report_date": "2026-06-16",
                "entries": [
                    {
                        "symbol": "600519",
                        "name": "Kweichow Moutai",
                        "operation_judgement": "incorrect",
                        "feedback_signal": "sell",
                        "feedback_score": 32.0,
                        "confidence": 0.82,
                        "risk_flags": ["thinking_incorrect"],
                        "rationale": "Buying into a negative same-day move was incorrect.",
                        "evidence": {"change_pct": -0.06},
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    engine._record_long_term_report(
        report_date="2026-06-15",
        report_type="weekly_analysis",
        week_id="2026-W25",
        report_markdown="# Weekly TradingAgents",
        candidates_snapshot=[
            {
                "symbol": "600519",
                "name": "Kweichow Moutai",
                "signal": "buy",
                "score": 86,
                "price": 100.0,
                "reason": "TradingAgents is bullish",
            }
        ],
    )
    monkeypatch.setattr(engine, "_get_price", lambda symbol: 103.0)
    monkeypatch.setattr(engine, "_fetch_news", AsyncMock(return_value=[]))
    monkeypatch.setattr(engine, "_get_technical_detail", AsyncMock(return_value={}))
    monkeypatch.setattr(engine, "_check_rules", AsyncMock(return_value=[]))

    result = await engine.run_daily_long_term_validation(date(2026, 6, 17))

    assert result["mode"] == "daily_optimization"
    payload = json.loads(
        (tmp_path / "reviews" / "2026-06-17" / "analysis.json").read_text(
            encoding="utf-8"
        )
    )
    row = payload["optimizations"][0]
    assert row["action"] == "hold"
    assert "thinking" in row["provider_breakdown"]
    assert row["provider_breakdown"]["thinking"]["signal"] == "sell"
    assert "thinking_incorrect" in row["risk_flags"]


def test_extract_kronos_signal_preserves_zero_forecast_return():
    signal = SimulationEngine._extract_kronos_signal(
        {
            "symbol": "600519",
            "name": "Kweichow Moutai",
            "price": 100.0,
            "kronos_prediction": {
                "forecast_return": 0.0,
                "confidence": 0.7,
            },
        }
    )

    assert signal is not None
    assert signal.normalized_signal() == "hold"
    assert signal.evidence["forecast_return"] == 0.0


def test_stopped_engine_skips_quant_execution(engine, monkeypatch):
    """Quant decisions should not execute simulated orders after the engine stops."""
    engine.start()
    engine.stop()
    called = False

    def fake_buy(*args, **kwargs):
        nonlocal called
        called = True
        return True, "should not run"

    monkeypatch.setattr(engine, "_execute_buy", fake_buy)
    decision = QuantDecision(
        symbol="600519",
        name="Kweichow Moutai",
        action="buy",
        signal="buy",
        score=80,
        target_weight=0.1,
        allocation_pct=0.1,
        executable=True,
        rationale="high confidence",
    )

    action_taken, action_reason = engine._execute_quant_decision(
        {"symbol": "600519", "name": "Kweichow Moutai"},
        decision,
    )

    assert called is False
    assert action_taken == "skipped"
    assert "已停止" in action_reason


@pytest.mark.asyncio
async def test_daily_optimization_generates_kronos_prediction_before_decision(
    engine, db, monkeypatch, tmp_path
):
    """Daily optimization should enrich weekly candidates with Kronos summaries."""

    class FakeKronosAdapter:
        def __init__(self):
            self.calls = []

        async def summarize_candidate(self, candidate, analysis_date):
            self.calls.append((candidate["symbol"], analysis_date.isoformat()))
            return {
                "forecast_return": -0.05,
                "confidence": 0.8,
                "horizon": "10d",
                "rationale": "Fake Kronos forecast is bearish",
            }

    fake_adapter = FakeKronosAdapter()
    engine.kronos_adapter = fake_adapter
    engine.review_output_dir = tmp_path / "reviews"
    engine._record_long_term_report(
        report_date="2026-06-15",
        report_type="weekly_analysis",
        week_id="2026-W25",
        report_markdown="# Weekly TradingAgents",
        candidates_snapshot=[
            {
                "symbol": "600519",
                "name": "Kweichow Moutai",
                "signal": "buy",
                "score": 86,
                "price": 100.0,
                "reason": "TradingAgents is bullish",
            }
        ],
    )
    monkeypatch.setattr(engine, "_get_price", lambda symbol: 101.0)
    monkeypatch.setattr(engine, "_fetch_news", AsyncMock(return_value=[]))
    monkeypatch.setattr(engine, "_get_technical_detail", AsyncMock(return_value={}))
    monkeypatch.setattr(engine, "_check_rules", AsyncMock(return_value=[]))

    await engine.run_daily_long_term_validation(date(2026, 6, 16))

    assert fake_adapter.calls == [("600519", "2026-06-16")]
    payload = json.loads(
        (tmp_path / "reviews" / "2026-06-16" / "analysis.json").read_text(
            encoding="utf-8"
        )
    )
    row = payload["optimizations"][0]
    assert row["action"] == "hold"
    assert "kronos_bearish_forecast" in row["risk_flags"]
    assert row["provider_breakdown"]["kronos"]["evidence"]["forecast_return"] == -0.05


@pytest.mark.asyncio
async def test_daily_optimization_continues_when_kronos_generation_fails(
    engine, db, monkeypatch, tmp_path
):
    """Kronos generation failure should not block simulated trading."""

    class FailingKronosAdapter:
        async def summarize_candidate(self, candidate, analysis_date):
            raise RuntimeError("model unavailable")

    engine.kronos_adapter = FailingKronosAdapter()
    engine.review_output_dir = tmp_path / "reviews"
    engine._record_long_term_report(
        report_date="2026-06-15",
        report_type="weekly_analysis",
        week_id="2026-W25",
        report_markdown="# Weekly TradingAgents",
        candidates_snapshot=[
            {
                "symbol": "600519",
                "name": "Kweichow Moutai",
                "signal": "buy",
                "score": 86,
                "price": 100.0,
                "reason": "TradingAgents is bullish",
            }
        ],
    )
    monkeypatch.setattr(engine, "_get_price", lambda symbol: 101.0)
    monkeypatch.setattr(engine, "_fetch_news", AsyncMock(return_value=[]))
    monkeypatch.setattr(engine, "_get_technical_detail", AsyncMock(return_value={}))
    monkeypatch.setattr(engine, "_check_rules", AsyncMock(return_value=[]))

    await engine.run_daily_long_term_validation(date(2026, 6, 16))

    payload = json.loads(
        (tmp_path / "reviews" / "2026-06-16" / "analysis.json").read_text(
            encoding="utf-8"
        )
    )
    row = payload["optimizations"][0]
    assert row["action"] == "buy"
    assert "kronos" not in row["provider_breakdown"]
