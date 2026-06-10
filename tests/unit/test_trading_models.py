"""模拟交易数据模型测试"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from src.trading.models import (
    SimAccount,
    SimPosition,
    SimTrade,
    SimDailyReport,
    SimAnalysisLog,
)


class TestSimAccount:
    """SimAccount 模型测试"""

    def test_create_minimal(self):
        """测试最小参数创建"""
        account = SimAccount(
            account_id="acc_001",
            initial_capital=100000.0,
            balance=100000.0,
            total_assets=100000.0,
        )
        assert account.account_id == "acc_001"
        assert account.initial_capital == 100000.0
        assert account.balance == 100000.0
        assert account.frozen == 0.0
        assert account.total_assets == 100000.0
        assert account.created_at is None
        assert account.updated_at is None

    def test_create_full(self):
        """测试完整参数创建"""
        now = datetime.now()
        account = SimAccount(
            account_id="acc_001",
            initial_capital=100000.0,
            balance=95000.0,
            frozen=5000.0,
            total_assets=102000.0,
            created_at=now,
            updated_at=now,
        )
        assert account.frozen == 5000.0
        assert account.created_at == now
        assert account.updated_at == now

    def test_frozen_default(self):
        """测试 frozen 默认值"""
        account = SimAccount(
            account_id="acc_001",
            initial_capital=100000.0,
            balance=100000.0,
            total_assets=100000.0,
        )
        assert account.frozen == 0.0

    def test_model_dump(self):
        """测试序列化"""
        account = SimAccount(
            account_id="acc_001",
            initial_capital=100000.0,
            balance=100000.0,
            total_assets=100000.0,
        )
        data = account.model_dump()
        assert data["account_id"] == "acc_001"
        assert data["frozen"] == 0.0

    def test_model_validate(self):
        """测试反序列化"""
        data = {
            "account_id": "acc_001",
            "initial_capital": 100000.0,
            "balance": 100000.0,
            "total_assets": 100000.0,
        }
        account = SimAccount.model_validate(data)
        assert account.account_id == "acc_001"


class TestSimPosition:
    """SimPosition 模型测试"""

    def test_create_minimal(self):
        """测试最小参数创建"""
        position = SimPosition(
            account_id="acc_001",
            symbol="600519",
            volume=100,
            avg_cost=1800.0,
        )
        assert position.account_id == "acc_001"
        assert position.symbol == "600519"
        assert position.volume == 100
        assert position.avg_cost == 1800.0
        assert position.current_price == 0.0
        assert position.market_value == 0.0
        assert position.pnl == 0.0
        assert position.pnl_pct == 0.0
        assert position.id is None
        assert position.name is None
        assert position.open_date is None
        assert position.updated_at is None

    def test_create_full(self):
        """测试完整参数创建"""
        now = datetime.now()
        position = SimPosition(
            id="pos_001",
            account_id="acc_001",
            symbol="600519",
            name="贵州茅台",
            volume=100,
            avg_cost=1800.0,
            current_price=1850.0,
            market_value=185000.0,
            pnl=5000.0,
            pnl_pct=2.78,
            open_date=date(2026, 1, 1),
            updated_at=now,
        )
        assert position.id == "pos_001"
        assert position.name == "贵州茅台"
        assert position.current_price == 1850.0
        assert position.pnl == 5000.0

    def test_defaults(self):
        """测试默认值"""
        position = SimPosition(
            account_id="acc_001",
            symbol="600519",
            volume=100,
            avg_cost=1800.0,
        )
        assert position.current_price == 0.0
        assert position.market_value == 0.0
        assert position.pnl == 0.0
        assert position.pnl_pct == 0.0

    def test_model_dump(self):
        """测试序列化"""
        position = SimPosition(
            account_id="acc_001",
            symbol="600519",
            volume=100,
            avg_cost=1800.0,
        )
        data = position.model_dump()
        assert data["symbol"] == "600519"
        assert data["current_price"] == 0.0


class TestSimTrade:
    """SimTrade 模型测试"""

    def test_create_minimal(self):
        """测试最小参数创建"""
        trade = SimTrade(
            trade_id="trade_001",
            account_id="acc_001",
            symbol="600519",
            side="buy",
            price=1800.0,
            volume=100,
            amount=180000.0,
        )
        assert trade.trade_id == "trade_001"
        assert trade.account_id == "acc_001"
        assert trade.symbol == "600519"
        assert trade.side == "buy"
        assert trade.price == 1800.0
        assert trade.volume == 100
        assert trade.amount == 180000.0
        assert trade.commission == 0.0
        assert trade.name is None
        assert trade.strategy is None
        assert trade.signal_score is None
        assert trade.signal_reason is None
        assert trade.created_at is None

    def test_create_full(self):
        """测试完整参数创建"""
        now = datetime.now()
        trade = SimTrade(
            trade_id="trade_001",
            account_id="acc_001",
            symbol="600519",
            name="贵州茅台",
            side="buy",
            price=1800.0,
            volume=100,
            amount=180000.0,
            commission=90.0,
            strategy="价值投资",
            signal_score=85.5,
            signal_reason="低估值+高ROE",
            created_at=now,
        )
        assert trade.name == "贵州茅台"
        assert trade.commission == 90.0
        assert trade.strategy == "价值投资"
        assert trade.signal_score == 85.5
        assert trade.signal_reason == "低估值+高ROE"
        assert trade.created_at == now

    def test_side_values(self):
        """测试 side 字段接受的值"""
        buy_trade = SimTrade(
            trade_id="t1",
            account_id="acc_001",
            symbol="600519",
            side="buy",
            price=1800.0,
            volume=100,
            amount=180000.0,
        )
        sell_trade = SimTrade(
            trade_id="t2",
            account_id="acc_001",
            symbol="600519",
            side="sell",
            price=1850.0,
            volume=100,
            amount=185000.0,
        )
        assert buy_trade.side == "buy"
        assert sell_trade.side == "sell"

    def test_commission_default(self):
        """测试 commission 默认值"""
        trade = SimTrade(
            trade_id="trade_001",
            account_id="acc_001",
            symbol="600519",
            side="buy",
            price=1800.0,
            volume=100,
            amount=180000.0,
        )
        assert trade.commission == 0.0


class TestSimDailyReport:
    """SimDailyReport 模型测试"""

    def test_create_minimal(self):
        """测试最小参数创建"""
        report = SimDailyReport(
            report_id="rpt_001",
            account_id="acc_001",
            report_date=date(2026, 6, 9),
        )
        assert report.report_id == "rpt_001"
        assert report.account_id == "acc_001"
        assert report.report_date == date(2026, 6, 9)
        assert report.total_assets is None
        assert report.daily_pnl is None
        assert report.daily_pnl_pct is None
        assert report.total_pnl is None
        assert report.total_pnl_pct is None
        assert report.max_drawdown is None
        assert report.win_rate is None
        assert report.trade_count is None
        assert report.report_markdown is None
        assert report.mistakes is None
        assert report.strategy_adjustments is None
        assert report.created_at is None

    def test_create_full(self):
        """测试完整参数创建"""
        now = datetime.now()
        report = SimDailyReport(
            report_id="rpt_001",
            account_id="acc_001",
            report_date=date(2026, 6, 9),
            total_assets=102000.0,
            daily_pnl=2000.0,
            daily_pnl_pct=2.0,
            total_pnl=2000.0,
            total_pnl_pct=2.0,
            max_drawdown=1.5,
            win_rate=0.6,
            trade_count=10,
            report_markdown="# 日报\n今日盈利2000元",
            mistakes="追高买入",
            strategy_adjustments="减少追高操作",
            created_at=now,
        )
        assert report.total_assets == 102000.0
        assert report.daily_pnl == 2000.0
        assert report.win_rate == 0.6
        assert report.mistakes == "追高买入"
        assert report.strategy_adjustments == "减少追高操作"


class TestSimAnalysisLog:
    """SimAnalysisLog 模型测试"""

    def test_create_minimal(self):
        """测试最小参数创建"""
        log = SimAnalysisLog(
            log_id="log_001",
            account_id="acc_001",
            symbol="600519",
            strategy="价值投资",
        )
        assert log.log_id == "log_001"
        assert log.account_id == "acc_001"
        assert log.symbol == "600519"
        assert log.strategy == "价值投资"
        assert log.score is None
        assert log.signal is None
        assert log.trend is None
        assert log.reason is None
        assert log.action_taken is None
        assert log.action_reason is None
        assert log.created_at is None

    def test_create_full(self):
        """测试完整参数创建"""
        now = datetime.now()
        log = SimAnalysisLog(
            log_id="log_001",
            account_id="acc_001",
            symbol="600519",
            strategy="价值投资",
            score=85.5,
            signal="buy",
            trend="up",
            reason="低估值+高ROE",
            action_taken="buy",
            action_reason="触发买入信号",
            created_at=now,
        )
        assert log.score == 85.5
        assert log.signal == "buy"
        assert log.trend == "up"
        assert log.reason == "低估值+高ROE"
        assert log.action_taken == "buy"
        assert log.action_reason == "触发买入信号"
        assert log.created_at == now

    def test_model_dump_roundtrip(self):
        """测试序列化/反序列化往返"""
        log = SimAnalysisLog(
            log_id="log_001",
            account_id="acc_001",
            symbol="600519",
            strategy="价值投资",
            score=85.5,
            signal="buy",
        )
        data = log.model_dump()
        restored = SimAnalysisLog.model_validate(data)
        assert restored.log_id == log.log_id
        assert restored.score == log.score
        assert restored.signal == log.signal
