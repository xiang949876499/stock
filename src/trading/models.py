"""模拟交易数据模型"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class SimAccount(BaseModel):
    """模拟账户"""

    account_id: str
    initial_capital: float
    balance: float
    frozen: float = 0.0
    total_assets: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SimPosition(BaseModel):
    """模拟持仓"""

    id: Optional[str] = None
    account_id: str
    symbol: str
    name: Optional[str] = None
    volume: int
    avg_cost: float
    current_price: float = 0.0
    market_value: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    open_date: Optional[date] = None
    updated_at: Optional[datetime] = None


class SimTrade(BaseModel):
    """模拟交易记录"""

    trade_id: str
    account_id: str
    symbol: str
    name: Optional[str] = None
    side: str
    price: float
    volume: int
    amount: float
    commission: float = 0.0
    strategy: Optional[str] = None
    signal_score: Optional[float] = None
    signal_reason: Optional[str] = None
    created_at: Optional[datetime] = None


class SimDailyReport(BaseModel):
    """模拟交易日报"""

    report_id: str
    account_id: str
    report_date: date
    total_assets: Optional[float] = None
    daily_pnl: Optional[float] = None
    daily_pnl_pct: Optional[float] = None
    total_pnl: Optional[float] = None
    total_pnl_pct: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    trade_count: Optional[int] = None
    report_markdown: Optional[str] = None
    mistakes: Optional[str] = None
    strategy_adjustments: Optional[str] = None
    created_at: Optional[datetime] = None


class SimAnalysisLog(BaseModel):
    """模拟分析日志"""

    log_id: str
    account_id: str
    symbol: str
    strategy: str
    score: Optional[float] = None
    signal: Optional[str] = None
    trend: Optional[str] = None
    reason: Optional[str] = None
    action_taken: Optional[str] = None
    action_reason: Optional[str] = None
    created_at: Optional[datetime] = None
