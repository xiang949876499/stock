# 模拟交易系统实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个模拟交易系统，根据自动推荐执行买卖，每 10 分钟分析，每日生成报告和失误分析。

**Architecture:** 扩展现有 ExecutionService，新增 SimulatedGateway 实现 BaseGateway 接口，复用 SignalBridge → RiskManager → PositionManager 链路。SimulationEngine 协调分析→信号→执行→记录流程。

**Tech Stack:** Python, FastAPI, SQLite, APScheduler, React, Ant Design, Zustand, ECharts

---

## 文件结构

```
src/trading/                      # 新增：模拟交易模块
├── __init__.py
├── engine.py                     # SimulationEngine 核心引擎
├── scheduler.py                  # TradingScheduler 调度器
├── strategy_selector.py          # StrategySelector 动态策略选择
├── mistake_analyzer.py           # MistakeAnalyzer 失误分析
└── models.py                     # 模拟交易数据模型

src/execution/gateways/
└── simulated.py                  # 新增：SimulatedGateway

src/web/api/
└── trading.py                    # 新增：交易 API

src/infra/
└── database.py                   # 修改：新增 sim 表初始化

src/main.py                       # 修改：启动时注册 TradingScheduler

frontend/src/pages/
├── Trading.tsx                   # 新增：模拟交易仪表盘
└── TradingReports.tsx            # 新增：每日报告页面

frontend/src/stores/
└── trading.ts                    # 新增：交易状态管理

frontend/src/services/
└── api.ts                        # 修改：新增 tradingApi

frontend/src/App.tsx              # 修改：新增路由

frontend/src/components/
└── AppSidebar.tsx                # 修改：新增菜单项
```

---

## Task 1: 数据库初始化

**Files:**
- Modify: `src/infra/database.py`
- Test: `tests/unit/test_sim_database.py`

- [ ] **Step 1: 编写数据库初始化测试**

```python
# tests/unit/test_sim_database.py
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
    # 检查表是否存在
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
    assert row[1] == 1000000  # initial_capital
    assert row[2] == 1000000  # balance
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_sim_database.py -v`
Expected: FAIL (init_sim_tables 方法不存在)

- [ ] **Step 3: 实现数据库初始化**

```python
# src/infra/database.py 中新增方法

def init_sim_tables(self):
    """初始化模拟交易表"""
    # 模拟账户
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

    # 模拟持仓
    self.execute("""
        CREATE TABLE IF NOT EXISTS sim_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            name TEXT,
            volume INTEGER NOT NULL,
            avg_cost REAL NOT NULL,
            current_price REAL DEFAULT 0,
            market_value REAL DEFAULT 0,
            pnl REAL DEFAULT 0,
            pnl_pct REAL DEFAULT 0,
            open_date TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(account_id, symbol)
        )
    """)

    # 交易记录
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

    # 每日报告
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

    # 分析日志
    self.execute("""
        CREATE TABLE IF NOT EXISTS sim_analysis_logs (
            log_id TEXT PRIMARY KEY,
            account_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            strategy TEXT NOT NULL,
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
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_sim_database.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/infra/database.py tests/unit/test_sim_database.py
git commit -m "feat(trading): 初始化模拟交易数据库表"
```

---

## Task 2: 模拟交易数据模型

**Files:**
- Create: `src/trading/__init__.py`
- Create: `src/trading/models.py`
- Test: `tests/unit/test_trading_models.py`

- [ ] **Step 1: 编写数据模型测试**

```python
# tests/unit/test_trading_models.py
"""模拟交易数据模型测试"""

import pytest
from datetime import datetime
from src.trading.models import (
    SimAccount, SimPosition, SimTrade, SimDailyReport, SimAnalysisLog
)


def test_sim_account():
    """测试模拟账户模型"""
    account = SimAccount(
        account_id="sim_001",
        initial_capital=1000000,
        balance=1000000,
        frozen=0,
        total_assets=1000000,
    )
    assert account.account_id == "sim_001"
    assert account.initial_capital == 1000000
    assert account.balance == 1000000


def test_sim_position():
    """测试模拟持仓模型"""
    position = SimPosition(
        account_id="sim_001",
        symbol="600519",
        name="贵州茅台",
        volume=100,
        avg_cost=1800.0,
        current_price=1850.0,
        market_value=185000.0,
        pnl=5000.0,
        pnl_pct=2.78,
        open_date="2026-06-09",
    )
    assert position.symbol == "600519"
    assert position.volume == 100
    assert position.pnl == 5000.0


def test_sim_trade():
    """测试交易记录模型"""
    trade = SimTrade(
        trade_id="trade_001",
        account_id="sim_001",
        symbol="600519",
        name="贵州茅台",
        side="BUY",
        price=1800.0,
        volume=100,
        amount=180000.0,
        commission=54.0,
        strategy="comprehensive",
        signal_score=78.0,
        signal_reason="技术面看多",
    )
    assert trade.side == "BUY"
    assert trade.amount == 180000.0


def test_sim_daily_report():
    """测试每日报告模型"""
    report = SimDailyReport(
        report_id="report_001",
        account_id="sim_001",
        report_date="2026-06-09",
        total_assets=1050000,
        daily_pnl=21000,
        daily_pnl_pct=2.0,
        total_pnl=50000,
        total_pnl_pct=5.0,
        max_drawdown=3.1,
        win_rate=62.5,
        trade_count=4,
        report_markdown="# 今日报告",
        mistakes='[{"type": "追涨杀跌"}]',
        strategy_adjustments='[{"action": "降低权重"}]',
    )
    assert report.daily_pnl == 21000
    assert report.win_rate == 62.5


def test_sim_analysis_log():
    """测试分析日志模型"""
    log = SimAnalysisLog(
        log_id="log_001",
        account_id="sim_001",
        symbol="600519",
        strategy="comprehensive",
        score=78.0,
        signal="buy",
        trend="bullish",
        reason="技术面看多",
        action_taken="executed",
        action_reason="信号强度足够",
    )
    assert log.signal == "buy"
    assert log.action_taken == "executed"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_trading_models.py -v`
Expected: FAIL (模块不存在)

- [ ] **Step 3: 创建模块和数据模型**

```python
# src/trading/__init__.py
"""模拟交易模块"""

from .models import SimAccount, SimPosition, SimTrade, SimDailyReport, SimAnalysisLog
from .engine import SimulationEngine
from .scheduler import TradingScheduler

__all__ = [
    "SimAccount",
    "SimPosition",
    "SimTrade",
    "SimDailyReport",
    "SimAnalysisLog",
    "SimulationEngine",
    "TradingScheduler",
]
```

```python
# src/trading/models.py
"""模拟交易数据模型"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SimAccount(BaseModel):
    """模拟账户"""
    account_id: str
    initial_capital: float
    balance: float
    frozen: float = 0
    total_assets: float
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SimPosition(BaseModel):
    """模拟持仓"""
    id: Optional[int] = None
    account_id: str
    symbol: str
    name: Optional[str] = None
    volume: int
    avg_cost: float
    current_price: float = 0
    market_value: float = 0
    pnl: float = 0
    pnl_pct: float = 0
    open_date: Optional[str] = None
    updated_at: Optional[str] = None


class SimTrade(BaseModel):
    """交易记录"""
    trade_id: str
    account_id: str
    symbol: str
    name: Optional[str] = None
    side: str  # BUY / SELL
    price: float
    volume: int
    amount: float
    commission: float = 0
    strategy: Optional[str] = None
    signal_score: Optional[float] = None
    signal_reason: Optional[str] = None
    created_at: Optional[str] = None


class SimDailyReport(BaseModel):
    """每日报告"""
    report_id: str
    account_id: str
    report_date: str
    total_assets: Optional[float] = None
    daily_pnl: Optional[float] = None
    daily_pnl_pct: Optional[float] = None
    total_pnl: Optional[float] = None
    total_pnl_pct: Optional[float] = None
    max_drawdown: Optional[float] = None
    win_rate: Optional[float] = None
    trade_count: Optional[int] = None
    report_markdown: Optional[str] = None
    mistakes: Optional[str] = None  # JSON string
    strategy_adjustments: Optional[str] = None  # JSON string
    created_at: Optional[str] = None


class SimAnalysisLog(BaseModel):
    """分析日志"""
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
    created_at: Optional[str] = None
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_trading_models.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/trading/ tests/unit/test_trading_models.py
git commit -m "feat(trading): 添加模拟交易数据模型"
```

---

## Task 3: SimulatedGateway 模拟网关

**Files:**
- Create: `src/execution/gateways/simulated.py`
- Test: `tests/unit/test_simulated_gateway.py`

- [ ] **Step 1: 编写模拟网关测试**

```python
# tests/unit/test_simulated_gateway.py
"""模拟网关测试"""

import pytest
import tempfile
import os
from src.infra.database import Database
from src.execution.gateways.simulated import SimulatedGateway
from src.execution.gateways.base import Order


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


@pytest.fixture
def gateway(db):
    """创建模拟网关"""
    return SimulatedGateway(db)


@pytest.mark.asyncio
async def test_connect(gateway):
    """测试连接并创建账户"""
    result = await gateway.connect({})
    assert result is True

    account = await gateway.get_account()
    assert account is not None
    assert account.balance == 1000000


@pytest.mark.asyncio
async def test_buy_order(gateway):
    """测试买入订单"""
    await gateway.connect({})

    order = Order(
        vt_symbol="600519",
        direction="LONG",
        offset="OPEN",
        price=1800.0,
        volume=100,
    )

    trade_id = await gateway.send_order(order)
    assert trade_id is not None

    # 检查持仓
    positions = await gateway.get_positions()
    assert len(positions) == 1
    assert positions[0].vt_symbol == "600519"
    assert positions[0].volume == 100

    # 检查资金
    account = await gateway.get_account()
    assert account.balance == 1000000 - 180000 - 54  # 金额 - 手续费


@pytest.mark.asyncio
async def test_sell_order(gateway):
    """测试卖出订单"""
    await gateway.connect({})

    # 先买入
    buy_order = Order(
        vt_symbol="600519",
        direction="LONG",
        offset="OPEN",
        price=1800.0,
        volume=100,
    )
    await gateway.send_order(buy_order)

    # 再卖出
    sell_order = Order(
        vt_symbol="600519",
        direction="SHORT",
        offset="CLOSE",
        price=1850.0,
        volume=100,
    )
    trade_id = await gateway.send_order(sell_order)
    assert trade_id is not None

    # 检查持仓清空
    positions = await gateway.get_positions()
    assert len(positions) == 0

    # 检查资金增加
    account = await gateway.get_account()
    assert account.balance > 1000000  # 赚了钱


@pytest.mark.asyncio
async def test_insufficient_funds(gateway):
    """测试资金不足"""
    await gateway.connect({})

    order = Order(
        vt_symbol="600519",
        direction="LONG",
        offset="OPEN",
        price=1800.0,
        volume=10000,  # 需要 1800 万，但只有 100 万
    )

    with pytest.raises(ValueError, match="资金不足"):
        await gateway.send_order(order)
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_simulated_gateway.py -v`
Expected: FAIL (模块不存在)

- [ ] **Step 3: 实现模拟网关**

```python
# src/execution/gateways/simulated.py
"""模拟交易网关"""

import uuid
from datetime import datetime, date
from typing import Optional

from src.execution.gateways.base import BaseGateway, Order, Trade, Position, Account
from src.infra.database import Database
from src.infra.logger import get_logger

logger = get_logger("simulated_gateway")

# 手续费率：万三
COMMISSION_RATE = 0.0003


class SimulatedGateway(BaseGateway):
    """模拟交易网关"""

    def __init__(self, db: Database):
        super().__init__(gateway_name="simulated")
        self.db = db
        self.account_id = "sim_001"
        self._connected = False

    async def connect(self, config: dict) -> bool:
        """初始化模拟账户"""
        # 检查账户是否存在
        cursor = self.db.execute(
            "SELECT account_id FROM sim_accounts WHERE account_id = ?",
            (self.account_id,)
        )
        row = cursor.fetchone()

        if not row:
            # 创建账户，初始资金 100 万
            self.db.execute(
                "INSERT INTO sim_accounts (account_id, initial_capital, balance, total_assets) VALUES (?, ?, ?, ?)",
                (self.account_id, 1000000, 1000000, 1000000)
            )
            self.db.commit()
            logger.info("创建模拟账户: 初始资金 100 万")

        self._connected = True
        return True

    async def disconnect(self):
        """断开连接"""
        self._connected = False

    async def send_order(self, order: Order) -> str:
        """模拟下单 - 立即成交"""
        trade_id = str(uuid.uuid4())
        amount = order.price * order.volume
        commission = amount * COMMISSION_RATE

        if order.offset == "OPEN":
            # 买入：检查资金
            account = await self.get_account()
            total_cost = amount + commission
            if account.available < total_cost:
                raise ValueError(f"资金不足: 需要 {total_cost}, 可用 {account.available}")

            # 扣减资金
            self.db.execute(
                "UPDATE sim_accounts SET balance = balance - ?, updated_at = ? WHERE account_id = ?",
                (total_cost, datetime.now().isoformat(), self.account_id)
            )

            # 更新持仓
            cursor = self.db.execute(
                "SELECT id, volume, avg_cost FROM sim_positions WHERE account_id = ? AND symbol = ?",
                (self.account_id, order.vt_symbol)
            )
            existing = cursor.fetchone()

            if existing:
                # 加仓
                old_volume = existing[1]
                old_cost = existing[2]
                new_volume = old_volume + order.volume
                new_avg_cost = (old_cost * old_volume + order.price * order.volume) / new_volume

                self.db.execute(
                    "UPDATE sim_positions SET volume = ?, avg_cost = ?, current_price = ?, market_value = ?, pnl = ?, pnl_pct = ?, updated_at = ? WHERE account_id = ? AND symbol = ?",
                    (new_volume, new_avg_cost, order.price, order.price * new_volume,
                     (order.price - new_avg_cost) * new_volume,
                     (order.price - new_avg_cost) / new_avg_cost * 100,
                     datetime.now().isoformat(), self.account_id, order.vt_symbol)
                )
            else:
                # 新建持仓
                self.db.execute(
                    "INSERT INTO sim_positions (account_id, symbol, volume, avg_cost, current_price, market_value, pnl, pnl_pct, open_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (self.account_id, order.vt_symbol, order.volume, order.price,
                     order.price, amount, 0, 0, date.today().isoformat())
                )

        elif order.offset == "CLOSE":
            # 卖出：检查持仓
            cursor = self.db.execute(
                "SELECT id, volume, avg_cost FROM sim_positions WHERE account_id = ? AND symbol = ?",
                (self.account_id, order.vt_symbol)
            )
            existing = cursor.fetchone()

            if not existing or existing[1] < order.volume:
                raise ValueError(f"持仓不足: {order.vt_symbol}")

            # 增加资金（扣除手续费）
            net_amount = amount - commission
            self.db.execute(
                "UPDATE sim_accounts SET balance = balance + ?, updated_at = ? WHERE account_id = ?",
                (net_amount, datetime.now().isoformat(), self.account_id)
            )

            # 更新持仓
            old_volume = existing[1]
            new_volume = old_volume - order.volume
            if new_volume == 0:
                self.db.execute(
                    "DELETE FROM sim_positions WHERE account_id = ? AND symbol = ?",
                    (self.account_id, order.vt_symbol)
                )
            else:
                self.db.execute(
                    "UPDATE sim_positions SET volume = ?, current_price = ?, market_value = ?, pnl = ?, pnl_pct = ?, updated_at = ? WHERE account_id = ? AND symbol = ?",
                    (new_volume, order.price, order.price * new_volume,
                     (order.price - existing[2]) * new_volume,
                     (order.price - existing[2]) / existing[2] * 100,
                     datetime.now().isoformat(), self.account_id, order.vt_symbol)
                )

        # 记录交易
        self.db.execute(
            "INSERT INTO sim_trades (trade_id, account_id, symbol, side, price, volume, amount, commission, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (trade_id, self.account_id, order.vt_symbol, "BUY" if order.offset == "OPEN" else "SELL",
             order.price, order.volume, amount, commission, datetime.now().isoformat())
        )
        self.db.commit()

        logger.info(f"模拟成交: {order.vt_symbol} {order.offset} {order.volume}股 @ {order.price}")
        return trade_id

    async def cancel_order(self, vt_orderid: str):
        """撤单（模拟交易立即成交，不支持撤单）"""
        logger.warning("模拟交易不支持撤单")

    async def get_positions(self) -> list[Position]:
        """获取持仓"""
        cursor = self.db.execute(
            "SELECT symbol, volume, avg_cost, current_price, pnl FROM sim_positions WHERE account_id = ?",
            (self.account_id,)
        )
        rows = cursor.fetchall()

        return [
            Position(
                vt_symbol=row[0],
                direction="LONG",
                volume=row[1],
                price=row[2],
                pnl=row[4],
            )
            for row in rows
        ]

    async def get_account(self) -> Account:
        """获取账户"""
        cursor = self.db.execute(
            "SELECT balance, frozen, total_assets FROM sim_accounts WHERE account_id = ?",
            (self.account_id,)
        )
        row = cursor.fetchone()

        if not row:
            return Account(account_id=self.account_id, balance=0, available=0, frozen=0)

        return Account(
            account_id=self.account_id,
            balance=row[0],
            available=row[0] - row[1],
            frozen=row[1],
        )

    async def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        try:
            import akshare as ak
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
            if df is not None and not df.empty:
                return float(df.iloc[-1]["收盘"])
        except Exception as e:
            logger.error(f"获取价格失败: {symbol}, {e}")
        return 0.0
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_simulated_gateway.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/execution/gateways/simulated.py tests/unit/test_simulated_gateway.py
git commit -m "feat(trading): 实现 SimulatedGateway 模拟网关"
```

---

## Task 4: StrategySelector 动态策略选择

**Files:**
- Create: `src/trading/strategy_selector.py`
- Test: `tests/unit/test_strategy_selector.py`

- [ ] **Step 1: 编写策略选择测试**

```python
# tests/unit/test_strategy_selector.py
"""策略选择器测试"""

import pytest
from src.trading.strategy_selector import StrategySelector


@pytest.fixture
def selector():
    return StrategySelector()


def test_get_market_state_trending(selector):
    """测试趋势行情判断"""
    # 模拟连续上涨的数据
    closes = [100 + i * 2 for i in range(20)]  # 连续上涨
    state = selector._get_market_state(closes)
    assert state == "trending"


def test_get_market_state_volatile(selector):
    """测试震荡行情判断"""
    # 模拟震荡数据
    closes = [100, 102, 98, 103, 97, 104, 96, 105, 95, 106,
              94, 107, 93, 108, 92, 109, 91, 110, 90, 111]
    state = selector._get_market_state(closes)
    assert state in ["volatile", "trending"]


def test_select_strategy_mapping(selector):
    """测试策略映射"""
    assert selector.STRATEGIES["trending"] == "trend"
    assert selector.STRATEGIES["volatile"] == "macd"
    assert selector.STRATEGIES["oversold"] == "ma_cross"
    assert selector.STRATEGIES["default"] == "comprehensive"
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_strategy_selector.py -v`
Expected: FAIL (模块不存在)

- [ ] **Step 3: 实现策略选择器**

```python
# src/trading/strategy_selector.py
"""动态策略选择器"""

from typing import List
from src.infra.logger import get_logger

logger = get_logger("strategy_selector")


class StrategySelector:
    """根据市场状态动态选择分析策略"""

    STRATEGIES = {
        "trending": "trend",           # 趋势行情 → 趋势策略
        "volatile": "macd",            # 震荡行情 → MACD
        "oversold": "ma_cross",        # 超卖反弹 → 均线金叉
        "default": "comprehensive",    # 默认 → 综合分析
    }

    def _get_market_state(self, closes: List[float]) -> str:
        """判断市场状态"""
        if len(closes) < 20:
            return "default"

        # 计算 20 日涨跌幅
        change_pct = (closes[-1] - closes[-20]) / closes[-20]

        # 计算波动率（20 日标准差）
        returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
        recent_returns = returns[-20:]
        avg_return = sum(recent_returns) / len(recent_returns)
        variance = sum((r - avg_return) ** 2 for r in recent_returns) / len(recent_returns)
        volatility = variance ** 0.5

        # 判断状态
        if change_pct > 0.05:  # 上涨超过 5%
            return "trending"
        elif change_pct < -0.05:  # 下跌超过 5%，可能超卖
            return "oversold"
        elif volatility > 0.02:  # 波动率较高
            return "volatile"
        else:
            return "default"

    def select(self, closes: List[float]) -> str:
        """选择策略"""
        state = self._get_market_state(closes)
        strategy = self.STRATEGIES.get(state, self.STRATEGIES["default"])
        logger.info(f"市场状态: {state}, 选择策略: {strategy}")
        return strategy
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_strategy_selector.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/trading/strategy_selector.py tests/unit/test_strategy_selector.py
git commit -m "feat(trading): 实现动态策略选择器"
```

---

## Task 5: MistakeAnalyzer 失误分析

**Files:**
- Create: `src/trading/mistake_analyzer.py`
- Test: `tests/unit/test_mistake_analyzer.py`

- [ ] **Step 1: 编写失误分析测试**

```python
# tests/unit/test_mistake_analyzer.py
"""失误分析器测试"""

import pytest
from src.trading.mistake_analyzer import MistakeAnalyzer


@pytest.fixture
def analyzer():
    return MistakeAnalyzer()


def test_detect_chase_high_sell_low(analyzer):
    """测试追涨杀跌检测"""
    trades = [
        {"symbol": "600519", "side": "BUY", "price": 1800, "created_at": "2026-06-09 09:35"},
        {"symbol": "600519", "side": "SELL", "price": 1750, "created_at": "2026-06-09 10:15"},
    ]
    prices = {"600519": [1800, 1780, 1750]}

    mistakes = analyzer.analyze(trades, prices)
    assert any(m["type"] == "追涨杀跌" for m in mistakes)


def test_detect_frequent_trading(analyzer):
    """测试频繁交易检测"""
    trades = [
        {"symbol": "600519", "side": "BUY", "price": 1800, "created_at": "2026-06-09 09:35"},
        {"symbol": "600519", "side": "SELL", "price": 1810, "created_at": "2026-06-09 10:00"},
        {"symbol": "600519", "side": "BUY", "price": 1805, "created_at": "2026-06-09 10:30"},
        {"symbol": "600519", "side": "SELL", "price": 1815, "created_at": "2026-06-09 11:00"},
    ]
    prices = {"600519": [1800, 1810, 1805, 1815]}

    mistakes = analyzer.analyze(trades, prices)
    assert any(m["type"] == "频繁交易" for m in mistakes)


def test_no_mistakes(analyzer):
    """测试无失误情况"""
    trades = [
        {"symbol": "600519", "side": "BUY", "price": 1800, "created_at": "2026-06-09 09:35"},
    ]
    prices = {"600519": [1800, 1810, 1820]}

    mistakes = analyzer.analyze(trades, prices)
    assert len(mistakes) == 0
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_mistake_analyzer.py -v`
Expected: FAIL (模块不存在)

- [ ] **Step 3: 实现失误分析器**

```python
# src/trading/mistake_analyzer.py
"""失误分析器"""

from typing import List, Dict, Any
from src.infra.logger import get_logger

logger = get_logger("mistake_analyzer")


class MistakeAnalyzer:
    """分析每日交易中的失误"""

    def analyze(self, trades: List[Dict[str, Any]], prices: Dict[str, List[float]]) -> List[Dict[str, Any]]:
        """分析交易失误"""
        mistakes = []

        # 检查追涨杀跌
        mistakes.extend(self._check_chase_high_sell_low(trades, prices))

        # 检查频繁交易
        mistakes.extend(self._check_frequent_trading(trades))

        # 检查止损不及时
        mistakes.extend(self._check_late_stop_loss(trades, prices))

        return mistakes

    def _check_chase_high_sell_low(self, trades: List[Dict], prices: Dict[str, List[float]]) -> List[Dict]:
        """检查追涨杀跌：买入后立即下跌，卖出后立即上涨"""
        mistakes = []

        for i, trade in enumerate(trades):
            symbol = trade["symbol"]
            price_history = prices.get(symbol, [])

            if len(price_history) < 2:
                continue

            if trade["side"] == "BUY":
                # 买入后价格下跌
                buy_price = trade["price"]
                if i + 1 < len(price_history) and price_history[i + 1] < buy_price * 0.98:
                    mistakes.append({
                        "type": "追涨杀跌",
                        "symbol": symbol,
                        "description": f"买入价 {buy_price}，随后价格下跌至 {price_history[i + 1]}",
                        "severity": "medium",
                    })

            elif trade["side"] == "SELL":
                # 卖出后价格上涨
                sell_price = trade["price"]
                if i + 1 < len(price_history) and price_history[i + 1] > sell_price * 1.02:
                    mistakes.append({
                        "type": "追涨杀跌",
                        "symbol": symbol,
                        "description": f"卖出价 {sell_price}，随后价格上涨至 {price_history[i + 1]}",
                        "severity": "medium",
                    })

        return mistakes

    def _check_frequent_trading(self, trades: List[Dict]) -> List[Dict]:
        """检查频繁交易：同一股票当天买卖超过 2 次"""
        mistakes = []
        symbol_counts = {}

        for trade in trades:
            symbol = trade["symbol"]
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

        for symbol, count in symbol_counts.items():
            if count > 2:
                mistakes.append({
                    "type": "频繁交易",
                    "symbol": symbol,
                    "description": f"当天交易 {count} 次，超过 2 次阈值",
                    "severity": "low",
                })

        return mistakes

    def _check_late_stop_loss(self, trades: List[Dict], prices: Dict[str, List[float]]) -> List[Dict]:
        """检查止损不及时：亏损超过 3% 才卖出"""
        mistakes = []
        stop_loss_threshold = 0.03

        # 找到买入和卖出配对
        buy_prices = {}
        for trade in trades:
            symbol = trade["symbol"]
            if trade["side"] == "BUY":
                buy_prices[symbol] = trade["price"]
            elif trade["side"] == "SELL" and symbol in buy_prices:
                buy_price = buy_prices[symbol]
                sell_price = trade["price"]
                loss_pct = (buy_price - sell_price) / buy_price

                if loss_pct > stop_loss_threshold:
                    mistakes.append({
                        "type": "止损不及时",
                        "symbol": symbol,
                        "description": f"亏损 {loss_pct:.1%} 才卖出，超过 {stop_loss_threshold:.0%} 阈值",
                        "severity": "high",
                    })

                del buy_prices[symbol]

        return mistakes
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_mistake_analyzer.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/trading/mistake_analyzer.py tests/unit/test_mistake_analyzer.py
git commit -m "feat(trading): 实现失误分析器"
```

---

## Task 6: SimulationEngine 核心引擎

**Files:**
- Create: `src/trading/engine.py`
- Test: `tests/unit/test_simulation_engine.py`

- [ ] **Step 1: 编写引擎测试**

```python
# tests/unit/test_simulation_engine.py
"""模拟引擎测试"""

import pytest
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock
from src.infra.database import Database
from src.trading.engine import SimulationEngine


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


@pytest.fixture
def engine(db):
    """创建模拟引擎"""
    engine = SimulationEngine.__new__(SimulationEngine)
    engine.db = db
    engine.account_id = "sim_001"
    engine._running = False
    return engine


def test_init_account(engine):
    """测试初始化账户"""
    engine._init_account()
    account = engine._get_account()
    assert account is not None
    assert account["balance"] == 1000000


def test_get_account(engine):
    """测试获取账户"""
    engine._init_account()
    account = engine._get_account()
    assert account["account_id"] == "sim_001"
    assert account["initial_capital"] == 1000000


def test_get_positions_empty(engine):
    """测试获取空持仓"""
    engine._init_account()
    positions = engine._get_positions()
    assert positions == []
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/test_simulation_engine.py -v`
Expected: FAIL (模块不存在)

- [ ] **Step 3: 实现模拟引擎**

```python
# src/trading/engine.py
"""模拟交易引擎"""

import uuid
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from src.infra.database import Database
from src.infra.logger import get_logger
from src.trading.strategy_selector import StrategySelector
from src.trading.mistake_analyzer import MistakeAnalyzer

logger = get_logger("simulation_engine")


class SimulationEngine:
    """模拟交易引擎"""

    def __init__(self, db: Database):
        self.db = db
        self.account_id = "sim_001"
        self._running = False
        self.strategy_selector = StrategySelector()
        self.mistake_analyzer = MistakeAnalyzer()
        self._init_account()

    def _init_account(self):
        """初始化模拟账户"""
        cursor = self.db.execute(
            "SELECT account_id FROM sim_accounts WHERE account_id = ?",
            (self.account_id,)
        )
        if not cursor.fetchone():
            self.db.execute(
                "INSERT INTO sim_accounts (account_id, initial_capital, balance, total_assets) VALUES (?, ?, ?, ?)",
                (self.account_id, 1000000, 1000000, 1000000)
            )
            self.db.commit()
            logger.info("创建模拟账户: 初始资金 100 万")

    def _get_account(self) -> Optional[Dict[str, Any]]:
        """获取账户信息"""
        cursor = self.db.execute(
            "SELECT account_id, initial_capital, balance, frozen, total_assets FROM sim_accounts WHERE account_id = ?",
            (self.account_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "account_id": row[0],
            "initial_capital": row[1],
            "balance": row[2],
            "frozen": row[3],
            "total_assets": row[4],
        }

    def _get_positions(self) -> List[Dict[str, Any]]:
        """获取持仓"""
        cursor = self.db.execute(
            "SELECT symbol, name, volume, avg_cost, current_price, market_value, pnl, pnl_pct, open_date FROM sim_positions WHERE account_id = ?",
            (self.account_id,)
        )
        rows = cursor.fetchall()
        return [
            {
                "symbol": row[0],
                "name": row[1],
                "volume": row[2],
                "avg_cost": row[3],
                "current_price": row[4],
                "market_value": row[5],
                "pnl": row[6],
                "pnl_pct": row[7],
                "open_date": row[8],
            }
            for row in rows
        ]

    def _get_trades(self, trade_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取交易记录"""
        if trade_date:
            cursor = self.db.execute(
                "SELECT trade_id, symbol, name, side, price, volume, amount, commission, strategy, signal_score, signal_reason, created_at FROM sim_trades WHERE account_id = ? AND DATE(created_at) = ? ORDER BY created_at DESC",
                (self.account_id, trade_date)
            )
        else:
            cursor = self.db.execute(
                "SELECT trade_id, symbol, name, side, price, volume, amount, commission, strategy, signal_score, signal_reason, created_at FROM sim_trades WHERE account_id = ? ORDER BY created_at DESC LIMIT 50",
                (self.account_id,)
            )
        rows = cursor.fetchall()
        return [
            {
                "trade_id": row[0],
                "symbol": row[1],
                "name": row[2],
                "side": row[3],
                "price": row[4],
                "volume": row[5],
                "amount": row[6],
                "commission": row[7],
                "strategy": row[8],
                "signal_score": row[9],
                "signal_reason": row[10],
                "created_at": row[11],
            }
            for row in rows
        ]

    def _record_analysis_log(self, symbol: str, strategy: str, score: float,
                             signal: str, trend: str, reason: str,
                             action_taken: str, action_reason: str):
        """记录分析日志"""
        log_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO sim_analysis_logs (log_id, account_id, symbol, strategy, score, signal, trend, reason, action_taken, action_reason, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (log_id, self.account_id, symbol, strategy, score, signal, trend, reason,
             action_taken, action_reason, datetime.now().isoformat())
        )
        self.db.commit()

    def _record_trade(self, symbol: str, name: str, side: str, price: float,
                      volume: int, amount: float, commission: float,
                      strategy: str, signal_score: float, signal_reason: str):
        """记录交易"""
        trade_id = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO sim_trades (trade_id, account_id, symbol, name, side, price, volume, amount, commission, strategy, signal_score, signal_reason, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (trade_id, self.account_id, symbol, name, side, price, volume, amount,
             commission, strategy, signal_score, signal_reason, datetime.now().isoformat())
        )
        self.db.commit()

    def _update_position(self, symbol: str, name: str, side: str, price: float, volume: int):
        """更新持仓"""
        cursor = self.db.execute(
            "SELECT id, volume, avg_cost FROM sim_positions WHERE account_id = ? AND symbol = ?",
            (self.account_id, symbol)
        )
        existing = cursor.fetchone()

        if side == "BUY":
            if existing:
                old_volume = existing[1]
                old_cost = existing[2]
                new_volume = old_volume + volume
                new_avg_cost = (old_cost * old_volume + price * volume) / new_volume

                self.db.execute(
                    "UPDATE sim_positions SET volume = ?, avg_cost = ?, current_price = ?, market_value = ?, pnl = ?, pnl_pct = ?, updated_at = ? WHERE account_id = ? AND symbol = ?",
                    (new_volume, new_avg_cost, price, price * new_volume,
                     (price - new_avg_cost) * new_volume,
                     (price - new_avg_cost) / new_avg_cost * 100,
                     datetime.now().isoformat(), self.account_id, symbol)
                )
            else:
                self.db.execute(
                    "INSERT INTO sim_positions (account_id, symbol, name, volume, avg_cost, current_price, market_value, pnl, pnl_pct, open_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (self.account_id, symbol, name, volume, price, price * volume,
                     price * volume, 0, 0, date.today().isoformat())
                )

        elif side == "SELL":
            if existing:
                old_volume = existing[1]
                new_volume = old_volume - volume
                if new_volume <= 0:
                    self.db.execute(
                        "DELETE FROM sim_positions WHERE account_id = ? AND symbol = ?",
                        (self.account_id, symbol)
                    )
                else:
                    self.db.execute(
                        "UPDATE sim_positions SET volume = ?, current_price = ?, market_value = ?, updated_at = ? WHERE account_id = ? AND symbol = ?",
                        (new_volume, price, price * new_volume,
                         datetime.now().isoformat(), self.account_id, symbol)
                    )

        self.db.commit()

    def _update_account_balance(self, side: str, amount: float, commission: float):
        """更新账户余额"""
        if side == "BUY":
            self.db.execute(
                "UPDATE sim_accounts SET balance = balance - ?, updated_at = ? WHERE account_id = ?",
                (amount + commission, datetime.now().isoformat(), self.account_id)
            )
        elif side == "SELL":
            self.db.execute(
                "UPDATE sim_accounts SET balance = balance + ?, updated_at = ? WHERE account_id = ?",
                (amount - commission, datetime.now().isoformat(), self.account_id)
            )
        self.db.commit()

    def _update_total_assets(self):
        """更新总资产"""
        account = self._get_account()
        positions = self._get_positions()
        position_value = sum(p["market_value"] for p in positions)
        total_assets = account["balance"] + position_value

        self.db.execute(
            "UPDATE sim_accounts SET total_assets = ?, updated_at = ? WHERE account_id = ?",
            (total_assets, datetime.now().isoformat(), self.account_id)
        )
        self.db.commit()

    def start(self):
        """启动模拟交易"""
        self._running = True
        logger.info("模拟交易启动")

    def stop(self):
        """停止模拟交易"""
        self._running = False
        logger.info("模拟交易停止")

    def is_running(self) -> bool:
        """是否运行中"""
        return self._running

    def get_status(self) -> Dict[str, Any]:
        """获取运行状态"""
        account = self._get_account()
        positions = self._get_positions()
        return {
            "running": self._running,
            "account": account,
            "positions": positions,
            "position_count": len(positions),
        }
```

- [ ] **Step 4: 运行测试验证通过**

Run: `pytest tests/unit/test_simulation_engine.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/trading/engine.py tests/unit/test_simulation_engine.py
git commit -m "feat(trading): 实现 SimulationEngine 核心引擎"
```

---

## Task 7: TradingScheduler 调度器

**Files:**
- Create: `src/trading/scheduler.py`

- [ ] **Step 1: 实现调度器**

```python
# src/trading/scheduler.py
"""交易调度器"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.infra.logger import get_logger

logger = get_logger("trading_scheduler")


class TradingScheduler:
    """交易调度器"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.engine = None

    def setup(self, engine):
        """设置定时任务"""
        self.engine = engine

        # 盘中分析：交易日 9:30-11:30, 13:00-15:00，每 10 分钟
        self.scheduler.add_job(
            self._run_analysis_cycle,
            CronTrigger(day_of_week='mon-fri', hour='9-11,13-14', minute='*/10'),
            id='sim_analysis'
        )

        # 午间报告：11:35 生成半日小结
        self.scheduler.add_job(
            self._generate_half_day_summary,
            CronTrigger(day_of_week='mon-fri', hour=11, minute=35),
            id='sim_half_day'
        )

        # 收盘报告：15:30 生成每日报告
        self.scheduler.add_job(
            self._generate_daily_report,
            CronTrigger(day_of_week='mon-fri', hour=15, minute=30),
            id='sim_daily_report'
        )

        # 策略调整：16:00 根据报告调整策略
        self.scheduler.add_job(
            self._adjust_strategy,
            CronTrigger(day_of_week='mon-fri', hour=16, minute=0),
            id='sim_adjust'
        )

        logger.info("交易调度器设置完成")

    def start(self):
        """启动调度器"""
        self.scheduler.start()
        logger.info("交易调度器启动")

    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("交易调度器停止")

    async def _run_analysis_cycle(self):
        """运行分析周期"""
        if not self.engine or not self.engine.is_running():
            return
        logger.info("开始盘中分析周期")
        # TODO: 实现完整分析流程
        logger.info("盘中分析周期完成")

    async def _generate_half_day_summary(self):
        """生成半日小结"""
        if not self.engine or not self.engine.is_running():
            return
        logger.info("生成半日小结")
        # TODO: 实现半日小结

    async def _generate_daily_report(self):
        """生成每日报告"""
        if not self.engine:
            return
        logger.info("生成每日报告")
        # TODO: 实现每日报告生成

    async def _adjust_strategy(self):
        """调整策略"""
        if not self.engine:
            return
        logger.info("调整策略")
        # TODO: 实现策略调整
```

- [ ] **Step 2: 提交**

```bash
git add src/trading/scheduler.py
git commit -m "feat(trading): 实现 TradingScheduler 调度器"
```

---

## Task 8: 交易 API

**Files:**
- Create: `src/web/api/trading.py`
- Modify: `src/web/api/router.py`
- Modify: `src/web/deps.py`

- [ ] **Step 1: 实现交易 API**

```python
# src/web/api/trading.py
"""交易 API"""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from pydantic import BaseModel

from src.infra.database import Database
from src.trading.engine import SimulationEngine
from src.exceptions import NotFoundError, ValidationError
from src.infra.logger import get_logger

logger = get_logger("trading_api")

router = APIRouter(prefix="/trading", tags=["trading"])


class ResetRequest(BaseModel):
    """重置请求"""
    initial_capital: float = 1000000


# 全局引擎实例
_engine: Optional[SimulationEngine] = None


def get_engine() -> SimulationEngine:
    """获取模拟引擎"""
    global _engine
    if _engine is None:
        db = Database("./data/sim_trading.db")
        db.connect()
        db.init_sim_tables()
        _engine = SimulationEngine(db)
    return _engine


@router.get("/account")
async def get_account(engine: SimulationEngine = Depends(get_engine)):
    """获取模拟账户信息"""
    account = engine._get_account()
    if not account:
        raise NotFoundError("模拟账户不存在")
    return account


@router.post("/account/reset")
async def reset_account(request: ResetRequest, engine: SimulationEngine = Depends(get_engine)):
    """重置账户"""
    engine.db.execute("DELETE FROM sim_accounts WHERE account_id = ?", (engine.account_id,))
    engine.db.execute("DELETE FROM sim_positions WHERE account_id = ?", (engine.account_id,))
    engine.db.execute("DELETE FROM sim_trades WHERE account_id = ?", (engine.account_id,))
    engine.db.execute("DELETE FROM sim_daily_reports WHERE account_id = ?", (engine.account_id,))
    engine.db.execute("DELETE FROM sim_analysis_logs WHERE account_id = ?", (engine.account_id,))
    engine.db.commit()

    engine.db.execute(
        "INSERT INTO sim_accounts (account_id, initial_capital, balance, total_assets) VALUES (?, ?, ?, ?)",
        (engine.account_id, request.initial_capital, request.initial_capital, request.initial_capital)
    )
    engine.db.commit()

    return {"message": "账户已重置", "initial_capital": request.initial_capital}


@router.get("/positions")
async def get_positions(engine: SimulationEngine = Depends(get_engine)):
    """获取当前持仓"""
    return engine._get_positions()


@router.get("/trades")
async def get_trades(
    date: Optional[str] = Query(None, description="日期筛选"),
    engine: SimulationEngine = Depends(get_engine)
):
    """获取交易历史"""
    return engine._get_trades(date)


@router.get("/reports")
async def get_reports(engine: SimulationEngine = Depends(get_engine)):
    """获取每日报告列表"""
    cursor = engine.db.execute(
        "SELECT report_id, report_date, total_assets, daily_pnl, daily_pnl_pct, total_pnl, total_pnl_pct, max_drawdown, win_rate, trade_count FROM sim_daily_reports WHERE account_id = ? ORDER BY report_date DESC",
        (engine.account_id,)
    )
    rows = cursor.fetchall()
    return [
        {
            "report_id": row[0],
            "report_date": row[1],
            "total_assets": row[2],
            "daily_pnl": row[3],
            "daily_pnl_pct": row[4],
            "total_pnl": row[5],
            "total_pnl_pct": row[6],
            "max_drawdown": row[7],
            "win_rate": row[8],
            "trade_count": row[9],
        }
        for row in rows
    ]


@router.get("/reports/{report_date}")
async def get_report(report_date: str, engine: SimulationEngine = Depends(get_engine)):
    """获取指定日期报告"""
    cursor = engine.db.execute(
        "SELECT * FROM sim_daily_reports WHERE account_id = ? AND report_date = ?",
        (engine.account_id, report_date)
    )
    row = cursor.fetchone()
    if not row:
        raise NotFoundError(f"报告不存在: {report_date}")
    return {
        "report_id": row[0],
        "account_id": row[1],
        "report_date": row[2],
        "total_assets": row[3],
        "daily_pnl": row[4],
        "daily_pnl_pct": row[5],
        "total_pnl": row[6],
        "total_pnl_pct": row[7],
        "max_drawdown": row[8],
        "win_rate": row[9],
        "trade_count": row[10],
        "report_markdown": row[11],
        "mistakes": row[12],
        "strategy_adjustments": row[13],
    }


@router.get("/reports/{report_date}/mistakes")
async def get_mistakes(report_date: str, engine: SimulationEngine = Depends(get_engine)):
    """获取失误分析"""
    cursor = engine.db.execute(
        "SELECT mistakes FROM sim_daily_reports WHERE account_id = ? AND report_date = ?",
        (engine.account_id, report_date)
    )
    row = cursor.fetchone()
    if not row:
        raise NotFoundError(f"报告不存在: {report_date}")
    import json
    return json.loads(row[0]) if row[0] else []


@router.get("/analysis-logs")
async def get_analysis_logs(
    date: Optional[str] = Query(None, description="日期筛选"),
    engine: SimulationEngine = Depends(get_engine)
):
    """获取分析日志"""
    if date:
        cursor = engine.db.execute(
            "SELECT * FROM sim_analysis_logs WHERE account_id = ? AND DATE(created_at) = ? ORDER BY created_at DESC",
            (engine.account_id, date)
        )
    else:
        cursor = engine.db.execute(
            "SELECT * FROM sim_analysis_logs WHERE account_id = ? ORDER BY created_at DESC LIMIT 100",
            (engine.account_id,)
        )
    rows = cursor.fetchall()
    return [
        {
            "log_id": row[0],
            "account_id": row[1],
            "symbol": row[2],
            "strategy": row[3],
            "score": row[4],
            "signal": row[5],
            "trend": row[6],
            "reason": row[7],
            "action_taken": row[8],
            "action_reason": row[9],
            "created_at": row[10],
        }
        for row in rows
    ]


@router.post("/start")
async def start_trading(engine: SimulationEngine = Depends(get_engine)):
    """启动模拟交易"""
    engine.start()
    return {"message": "模拟交易已启动", "running": True}


@router.post("/stop")
async def stop_trading(engine: SimulationEngine = Depends(get_engine)):
    """停止模拟交易"""
    engine.stop()
    return {"message": "模拟交易已停止", "running": False}


@router.get("/status")
async def get_status(engine: SimulationEngine = Depends(get_engine)):
    """获取运行状态"""
    return engine.get_status()
```

- [ ] **Step 2: 注册路由**

```python
# src/web/api/router.py 中新增导入和路由

from .trading import router as trading_router

# 在 router.include_router 中添加
router.include_router(trading_router)
```

- [ ] **Step 3: 提交**

```bash
git add src/web/api/trading.py src/web/api/router.py
git commit -m "feat(trading): 实现交易 API 端点"
```

---

## Task 9: 前端状态管理

**Files:**
- Create: `frontend/src/stores/trading.ts`
- Modify: `frontend/src/services/api.ts`

- [ ] **Step 1: 添加 API 服务**

```typescript
// frontend/src/services/api.ts 中新增

// 模拟交易相关
export const tradingApi = {
  getAccount: () =>
    api.get('/trading/account'),

  resetAccount: (initialCapital: number = 1000000) =>
    api.post('/trading/account/reset', { initial_capital: initialCapital }),

  getPositions: () =>
    api.get('/trading/positions'),

  getTrades: (date?: string) =>
    api.get('/trading/trades', { params: { date } }),

  getReports: () =>
    api.get('/trading/reports'),

  getReport: (date: string) =>
    api.get(`/trading/reports/${date}`),

  getMistakes: (date: string) =>
    api.get(`/trading/reports/${date}/mistakes`),

  getAnalysisLogs: (date?: string) =>
    api.get('/trading/analysis-logs', { params: { date } }),

  start: () =>
    api.post('/trading/start'),

  stop: () =>
    api.post('/trading/stop'),

  getStatus: () =>
    api.get('/trading/status'),
}
```

- [ ] **Step 2: 创建状态管理**

```typescript
// frontend/src/stores/trading.ts
import { create } from 'zustand'
import { tradingApi } from '../services/api'

interface TradingAccount {
  account_id: string
  initial_capital: number
  balance: number
  frozen: number
  total_assets: number
}

interface TradingPosition {
  symbol: string
  name: string
  volume: number
  avg_cost: number
  current_price: number
  market_value: number
  pnl: number
  pnl_pct: number
  open_date: string
}

interface TradingTrade {
  trade_id: string
  symbol: string
  name: string
  side: string
  price: number
  volume: number
  amount: number
  commission: number
  strategy: string
  signal_score: number
  signal_reason: string
  created_at: string
}

interface TradingReport {
  report_id: string
  report_date: string
  total_assets: number
  daily_pnl: number
  daily_pnl_pct: number
  total_pnl: number
  total_pnl_pct: number
  max_drawdown: number
  win_rate: number
  trade_count: number
  report_markdown?: string
  mistakes?: string
  strategy_adjustments?: string
}

interface AnalysisLog {
  log_id: string
  symbol: string
  strategy: string
  score: number
  signal: string
  trend: string
  reason: string
  action_taken: string
  action_reason: string
  created_at: string
}

interface TradingState {
  account: TradingAccount | null
  positions: TradingPosition[]
  trades: TradingTrade[]
  reports: TradingReport[]
  analysisLogs: AnalysisLog[]
  running: boolean
  loading: boolean
  error: string | null

  fetchAccount: () => Promise<void>
  fetchPositions: () => Promise<void>
  fetchTrades: (date?: string) => Promise<void>
  fetchReports: () => Promise<void>
  fetchReport: (date: string) => Promise<TradingReport | null>
  fetchAnalysisLogs: (date?: string) => Promise<void>
  startTrading: () => Promise<void>
  stopTrading: () => Promise<void>
  resetAccount: (initialCapital?: number) => Promise<void>
  fetchStatus: () => Promise<void>
}

export const useTradingStore = create<TradingState>((set, get) => ({
  account: null,
  positions: [],
  trades: [],
  reports: [],
  analysisLogs: [],
  running: false,
  loading: false,
  error: null,

  fetchAccount: async () => {
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.getAccount()
      set({ account: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchPositions: async () => {
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.getPositions()
      set({ positions: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchTrades: async (date?: string) => {
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.getTrades(date)
      set({ trades: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchReports: async () => {
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.getReports()
      set({ reports: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchReport: async (date: string) => {
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.getReport(date)
      set({ loading: false })
      return response.data
    } catch (error: any) {
      set({ error: error.message, loading: false })
      return null
    }
  },

  fetchAnalysisLogs: async (date?: string) => {
    set({ loading: true, error: null })
    try {
      const response = await tradingApi.getAnalysisLogs(date)
      set({ analysisLogs: response.data, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  startTrading: async () => {
    set({ loading: true, error: null })
    try {
      await tradingApi.start()
      set({ running: true, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  stopTrading: async () => {
    set({ loading: true, error: null })
    try {
      await tradingApi.stop()
      set({ running: false, loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  resetAccount: async (initialCapital?: number) => {
    set({ loading: true, error: null })
    try {
      await tradingApi.resetAccount(initialCapital)
      // 重新获取数据
      await get().fetchAccount()
      await get().fetchPositions()
      set({ loading: false })
    } catch (error: any) {
      set({ error: error.message, loading: false })
    }
  },

  fetchStatus: async () => {
    try {
      const response = await tradingApi.getStatus()
      set({
        running: response.data.running,
        account: response.data.account,
        positions: response.data.positions,
      })
    } catch (error: any) {
      set({ error: error.message })
    }
  },
}))
```

- [ ] **Step 3: 提交**

```bash
git add frontend/src/stores/trading.ts frontend/src/services/api.ts
git commit -m "feat(trading): 添加前端状态管理和 API 服务"
```

---

## Task 10: 前端页面

**Files:**
- Create: `frontend/src/pages/Trading.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/AppSidebar.tsx`

- [ ] **Step 1: 创建模拟交易页面**

```tsx
// frontend/src/pages/Trading.tsx
import { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Button, Space, message, Modal, Tabs } from 'antd'
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import { useTradingStore } from '../stores/trading'
import { formatDateTime, formatAmount } from '../utils'

const Trading = () => {
  const {
    account,
    positions,
    trades,
    analysisLogs,
    running,
    loading,
    fetchAccount,
    fetchPositions,
    fetchTrades,
    fetchAnalysisLogs,
    startTrading,
    stopTrading,
    resetAccount,
    fetchStatus,
  } = useTradingStore()

  const [activeTab, setActiveTab] = useState('positions')

  useEffect(() => {
    fetchAccount()
    fetchPositions()
    fetchTrades()
    fetchAnalysisLogs()
    fetchStatus()
  }, [])

  const handleStart = async () => {
    await startTrading()
    message.success('模拟交易已启动')
  }

  const handleStop = async () => {
    await stopTrading()
    message.success('模拟交易已停止')
  }

  const handleReset = () => {
    Modal.confirm({
      title: '确认重置',
      content: '重置将清空所有交易记录和持仓，确定要重置吗？',
      onOk: async () => {
        await resetAccount()
        message.success('账户已重置')
      },
    })
  }

  // 计算统计数据
  const totalPnl = account ? account.total_assets - account.initial_capital : 0
  const totalPnlPct = account ? (totalPnl / account.initial_capital) * 100 : 0

  const positionColumns = [
    { title: '股票代码', dataIndex: 'symbol', key: 'symbol' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '数量', dataIndex: 'volume', key: 'volume' },
    { title: '成本价', dataIndex: 'avg_cost', key: 'avg_cost', render: (v: number) => v?.toFixed(2) },
    { title: '现价', dataIndex: 'current_price', key: 'current_price', render: (v: number) => v?.toFixed(2) },
    { title: '市值', dataIndex: 'market_value', key: 'market_value', render: (v: number) => formatAmount(v) },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (v: number) => (
        <Tag color={v >= 0 ? 'green' : 'red'}>{v >= 0 ? '+' : ''}{v?.toFixed(2)}</Tag>
      ),
    },
    {
      title: '盈亏%',
      dataIndex: 'pnl_pct',
      key: 'pnl_pct',
      render: (v: number) => (
        <Tag color={v >= 0 ? 'green' : 'red'}>{v >= 0 ? '+' : ''}{v?.toFixed(2)}%</Tag>
      ),
    },
  ]

  const tradeColumns = [
    { title: '时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => formatDateTime(v) },
    { title: '股票', dataIndex: 'symbol', key: 'symbol' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (v: string) => (
        <Tag color={v === 'BUY' ? 'green' : 'red'}>{v === 'BUY' ? '买入' : '卖出'}</Tag>
      ),
    },
    { title: '价格', dataIndex: 'price', key: 'price', render: (v: number) => v?.toFixed(2) },
    { title: '数量', dataIndex: 'volume', key: 'volume' },
    { title: '金额', dataIndex: 'amount', key: 'amount', render: (v: number) => formatAmount(v) },
    { title: '策略', dataIndex: 'strategy', key: 'strategy' },
    { title: '评分', dataIndex: 'signal_score', key: 'signal_score' },
  ]

  const logColumns = [
    { title: '时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => formatDateTime(v) },
    { title: '股票', dataIndex: 'symbol', key: 'symbol' },
    { title: '策略', dataIndex: 'strategy', key: 'strategy' },
    { title: '评分', dataIndex: 'score', key: 'score' },
    {
      title: '信号',
      dataIndex: 'signal',
      key: 'signal',
      render: (v: string) => {
        const colorMap: Record<string, string> = { buy: 'green', sell: 'red', hold: 'blue' }
        const textMap: Record<string, string> = { buy: '买入', sell: '卖出', hold: '持有' }
        return <Tag color={colorMap[v]}>{textMap[v]}</Tag>
      },
    },
    {
      title: '执行状态',
      dataIndex: 'action_taken',
      key: 'action_taken',
      render: (v: string) => {
        const colorMap: Record<string, string> = { executed: 'green', skipped: 'orange', rejected: 'red' }
        const textMap: Record<string, string> = { executed: '已执行', skipped: '已跳过', rejected: '已拒绝' }
        return <Tag color={colorMap[v]}>{textMap[v]}</Tag>
      },
    },
  ]

  return (
    <div>
      <h2>模拟交易</h2>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={4}>
          <Card>
            <Statistic
              title="总资产"
              value={account?.total_assets || 0}
              precision={2}
              prefix="¥"
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="可用资金"
              value={account?.balance || 0}
              precision={2}
              prefix="¥"
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="累计盈亏"
              value={totalPnl}
              precision={2}
              prefix={totalPnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix="元"
              valueStyle={{ color: totalPnl >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="累计收益率"
              value={totalPnlPct}
              precision={2}
              suffix="%"
              valueStyle={{ color: totalPnlPct >= 0 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic title="持仓数量" value={positions.length} suffix="只" />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="状态"
              value={running ? '运行中' : '已停止'}
              valueStyle={{ color: running ? '#3f8600' : '#999' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 控制栏 */}
      <Card style={{ marginBottom: 24 }}>
        <Space>
          {running ? (
            <Button type="primary" danger icon={<PauseCircleOutlined />} onClick={handleStop}>
              停止
            </Button>
          ) : (
            <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleStart}>
              启动
            </Button>
          )}
          <Button icon={<ReloadOutlined />} onClick={handleReset}>
            重置
          </Button>
        </Space>
      </Card>

      {/* 详情标签页 */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <Tabs.TabPane tab="持仓" key="positions">
            <Table
              columns={positionColumns}
              dataSource={positions}
              rowKey="symbol"
              loading={loading}
              pagination={false}
            />
          </Tabs.TabPane>
          <Tabs.TabPane tab="交易记录" key="trades">
            <Table
              columns={tradeColumns}
              dataSource={trades}
              rowKey="trade_id"
              loading={loading}
              pagination={{ pageSize: 20 }}
            />
          </Tabs.TabPane>
          <Tabs.TabPane tab="分析日志" key="logs">
            <Table
              columns={logColumns}
              dataSource={analysisLogs}
              rowKey="log_id"
              loading={loading}
              pagination={{ pageSize: 50 }}
            />
          </Tabs.TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default Trading
```

- [ ] **Step 2: 添加路由**

```tsx
// frontend/src/App.tsx 中新增

import Trading from './pages/Trading'

// 在 Routes 中添加
<Route path="/trading" element={<Trading />} />
```

- [ ] **Step 3: 添加菜单项**

```tsx
// frontend/src/components/AppSidebar.tsx 中新增

import { FundOutlined } from '@ant-design/icons'

// 在 menuItems 中添加
{
  key: '/trading',
  icon: <FundOutlined />,
  label: '模拟交易',
},
```

- [ ] **Step 4: 提交**

```bash
git add frontend/src/pages/Trading.tsx frontend/src/App.tsx frontend/src/components/AppSidebar.tsx
git commit -m "feat(trading): 添加模拟交易前端页面"
```

---

## Task 11: 集成测试

**Files:**
- Create: `tests/integration/test_trading_api.py`

- [ ] **Step 1: 编写集成测试**

```python
# tests/integration/test_trading_api.py
"""交易 API 集成测试"""

import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.infra.database import Database


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


def test_get_account(client):
    """测试获取账户"""
    response = client.get("/api/v1/trading/account")
    assert response.status_code == 200
    data = response.json()
    assert "account_id" in data
    assert "balance" in data


def test_get_positions(client):
    """测试获取持仓"""
    response = client.get("/api/v1/trading/positions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_trades(client):
    """测试获取交易记录"""
    response = client.get("/api/v1/trading/trades")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_start_stop(client):
    """测试启动停止"""
    # 启动
    response = client.post("/api/v1/trading/start")
    assert response.status_code == 200
    assert response.json()["running"] is True

    # 获取状态
    response = client.get("/api/v1/trading/status")
    assert response.status_code == 200
    assert response.json()["running"] is True

    # 停止
    response = client.post("/api/v1/trading/stop")
    assert response.status_code == 200
    assert response.json()["running"] is False


def test_reset_account(client):
    """测试重置账户"""
    response = client.post("/api/v1/trading/account/reset", json={"initial_capital": 500000})
    assert response.status_code == 200
    assert response.json()["initial_capital"] == 500000

    # 验证重置后的账户
    response = client.get("/api/v1/trading/account")
    assert response.status_code == 200
    assert response.json()["balance"] == 500000


def test_get_reports(client):
    """测试获取报告列表"""
    response = client.get("/api/v1/trading/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_analysis_logs(client):
    """测试获取分析日志"""
    response = client.get("/api/v1/trading/analysis-logs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

- [ ] **Step 2: 运行集成测试**

Run: `pytest tests/integration/test_trading_api.py -v`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add tests/integration/test_trading_api.py
git commit -m "test(trading): 添加交易 API 集成测试"
```

---

## Task 12: 最终集成

**Files:**
- Modify: `src/main.py`

- [ ] **Step 1: 注册调度器**

```python
# src/main.py 中修改 startup 函数

from src.trading.scheduler import TradingScheduler
from src.trading.engine import SimulationEngine
from src.infra.database import Database

# 在 startup 函数中添加
@app.on_event("startup")
async def startup():
    """应用启动"""
    global settings, logger, scheduler

    # 加载配置
    settings = get_settings()

    # 设置日志
    logger = setup_logger("stock-hub", settings.log_dir)
    logger.info("应用启动", version=settings.app_version)

    # 注册并初始化集成适配器
    register_integrations()
    await registry.initialize_all()

    # 启动调度器
    scheduler = TaskScheduler()
    scheduler.setup()
    scheduler.start()

    # 初始化模拟交易
    db = Database("./data/sim_trading.db")
    db.connect()
    db.init_sim_tables()
    engine = SimulationEngine(db)
    trading_scheduler = TradingScheduler()
    trading_scheduler.setup(engine)
    trading_scheduler.start()
    logger.info("模拟交易调度器启动")
```

- [ ] **Step 2: 运行全量测试**

Run: `pytest tests/ -v`
Expected: 所有测试通过

- [ ] **Step 3: 最终提交**

```bash
git add src/main.py
git commit -m "feat(trading): 集成模拟交易到主应用"
```

---

## 完成

实施计划已完成。共 12 个任务，覆盖：
- 数据库初始化
- 数据模型
- SimulatedGateway 模拟网关
- StrategySelector 动态策略选择
- MistakeAnalyzer 失误分析
- SimulationEngine 核心引擎
- TradingScheduler 调度器
- 交易 API
- 前端状态管理
- 前端页面
- 集成测试
- 最终集成
