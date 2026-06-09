# 模拟交易系统设计文档

**日期**: 2026-06-09
**状态**: 设计完成，待实现
**作者**: Claude + 用户协作

---

## 1. 概述

### 1.1 需求

构建一个模拟交易系统，核心功能：

- 根据自动推荐的股票池，执行买入/卖出操作
- 交易时间内每 10 分钟分析一次，动态选择策略
- 每天收盘后生成分析报告和交易记录
- 分析当天交易是否存在失误，加入报告
- 每天根据报告调整策略
- 初始资金 100 万元人民币

### 1.2 设计方案

扩展现有 `ExecutionService`，新增 `SimulatedGateway`（模拟网关），复用 `SignalBridge` → `RiskManager` → `PositionManager` 的完整链路。

---

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    TradingScheduler (调度器)                   │
│  盘中: 每 10 分钟触发分析 → 生成信号 → 执行模拟交易            │
│  收盘: 生成每日报告 → 分析失误 → 调整策略                      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  SimulationEngine (核心引擎)                   │
│  协调: AnalysisService → SignalBridge → SimulatedGateway     │
│  管理: 策略选择、信号聚合、交易执行、记录保存                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│AnalysisService│  │ SignalBridge  │  │SimulatedGateway│
│ (现有: 分析)    │  │ (现有: 信号→订单)│  │ (新增: 模拟执行) │
└──────────────┘  └──────────────┘  └──────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLite 数据库                               │
│  tables: sim_accounts, sim_positions, sim_trades,            │
│          sim_daily_reports, sim_analysis_logs                │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 设计原则

1. **最大复用** — 复用现有 ExecutionService、SignalBridge、RiskManager、PositionManager
2. **Gateway 隔离** — SimulatedGateway 实现 BaseGateway 接口，未来可替换为实盘
3. **调度驱动** — 使用 APScheduler 定时触发，与现有 TaskScheduler 集成
4. **数据持久化** — SQLite 存储所有交易数据，同时导出 Markdown 报告

---

## 3. 数据库设计

数据库路径: `data/sim_trading.db`

### 3.1 sim_accounts（模拟账户）

```sql
CREATE TABLE sim_accounts (
    account_id TEXT PRIMARY KEY,
    initial_capital REAL NOT NULL,      -- 初始资金 1000000
    balance REAL NOT NULL,              -- 可用资金
    frozen REAL DEFAULT 0,              -- 冻结资金
    total_assets REAL NOT NULL,         -- 总资产 = balance + 持仓市值
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 sim_positions（模拟持仓）

```sql
CREATE TABLE sim_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT,
    volume INTEGER NOT NULL,            -- 持仓数量
    avg_cost REAL NOT NULL,             -- 成本价
    current_price REAL DEFAULT 0,       -- 当前价
    market_value REAL DEFAULT 0,        -- 市值
    pnl REAL DEFAULT 0,                 -- 浮动盈亏
    pnl_pct REAL DEFAULT 0,             -- 浮动盈亏%
    open_date TEXT,                     -- 开仓日期
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, symbol)
);
```

### 3.3 sim_trades（交易记录）

```sql
CREATE TABLE sim_trades (
    trade_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT,
    side TEXT NOT NULL,                 -- BUY / SELL
    price REAL NOT NULL,
    volume INTEGER NOT NULL,
    amount REAL NOT NULL,               -- 成交金额
    commission REAL DEFAULT 0,          -- 手续费
    strategy TEXT,                      -- 触发策略
    signal_score REAL,                  -- 信号评分
    signal_reason TEXT,                 -- 信号原因
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### 3.4 sim_daily_reports（每日报告）

```sql
CREATE TABLE sim_daily_reports (
    report_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    report_date TEXT NOT NULL,
    total_assets REAL,
    daily_pnl REAL,                     -- 当日盈亏
    daily_pnl_pct REAL,                 -- 当日收益率
    total_pnl REAL,                     -- 累计盈亏
    total_pnl_pct REAL,                 -- 累计收益率
    max_drawdown REAL,                  -- 最大回撤
    win_rate REAL,                      -- 胜率
    trade_count INTEGER,                -- 交易次数
    report_markdown TEXT,               -- Markdown 报告内容
    mistakes TEXT,                      -- 失误分析 JSON
    strategy_adjustments TEXT,          -- 策略调整 JSON
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, report_date)
);
```

### 3.5 sim_analysis_logs（分析日志）

```sql
CREATE TABLE sim_analysis_logs (
    log_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    score REAL,
    signal TEXT,                        -- buy/sell/hold
    trend TEXT,                         -- bullish/bearish/neutral
    reason TEXT,
    action_taken TEXT,                  -- executed/skipped/rejected
    action_reason TEXT,                 -- 为什么执行/跳过
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. 核心模块设计

### 4.1 SimulatedGateway（模拟网关）

**位置**: `src/execution/gateways/simulated.py`

实现 `BaseGateway` 接口，模拟买卖立即成交。

```python
class SimulatedGateway(BaseGateway):
    """模拟交易网关"""

    def __init__(self, db: Database):
        self.db = db
        self.account_id = "sim_001"
        self._connected = False

    async def connect(self, config: dict) -> bool:
        """初始化模拟账户（如果不存在）"""

    async def send_order(self, order: Order) -> str:
        """模拟下单 - 立即成交
        1. 检查资金/持仓是否足够
        2. 扣减/增加资金
        3. 更新持仓
        4. 写入 sim_trades 表
        5. 返回 trade_id
        """

    async def get_positions(self) -> list[Position]:
        """从数据库读取持仓"""

    async def get_account(self) -> Account:
        """从数据库读取账户"""

    async def get_current_price(self, symbol: str) -> float:
        """获取当前价格（从 akshare）"""
```

### 4.2 SimulationEngine（模拟引擎）

**位置**: `src/trading/engine.py`

协调分析→信号→执行→记录的完整流程。

```python
class SimulationEngine:
    """模拟交易引擎"""

    def __init__(self):
        self.db = Database("./data/sim_trading.db")
        self.gateway = SimulatedGateway(self.db)
        self.execution_service = ExecutionService()
        self.analysis_service = AnalysisService(ai_adapter)
        self.report_generator = ReportGenerator(ai_adapter)

    async def run_analysis_cycle(self):
        """每 10 分钟的分析周期
        1. 获取股票池（推荐 + 持仓）
        2. 动态选择策略
        3. 逐只分析，生成信号
        4. 聚合信号，生成 Signal
        5. 通过 SignalBridge 生成订单
        6. 通过 SimulatedGateway 执行
        7. 记录 sim_analysis_logs
        """

    async def generate_daily_report(self):
        """收盘后生成每日报告
        1. 计算当日盈亏、累计收益、最大回撤、胜率
        2. 分析失误（追涨杀跌、错过机会、止损不及时等）
        3. 生成策略调整建议
        4. 保存 Markdown + 写入 sim_daily_reports
        """

    async def adjust_strategy(self):
        """根据每日报告调整策略权重"""
```

### 4.3 StrategySelector（动态策略选择器）

**位置**: `src/trading/strategy_selector.py`

根据市场状态动态选择分析策略。

```python
class StrategySelector:
    """动态策略选择器"""

    STRATEGIES = {
        "trending": "trend",           # 趋势行情 → 趋势策略
        "volatile": "macd",            # 震荡行情 → MACD
        "oversold": "ma_cross",        # 超卖反弹 → 均线金叉
        "default": "comprehensive",    # 默认 → 综合分析
    }

    async def select(self, symbol: str, market: str) -> str:
        """根据市场状态选择策略
        1. 获取近 20 日 K 线
        2. 计算波动率、趋势强度
        3. 判断市场状态
        4. 返回策略名称
        """
```

### 4.4 MistakeAnalyzer（失误分析器）

**位置**: `src/trading/mistake_analyzer.py`

分析每日交易中的失误。

```python
class MistakeAnalyzer:
    """失误分析器"""

    async def analyze(self, trades: list, prices: dict) -> list[dict]:
        """分析当日交易失误
        1. 追涨杀跌：买入后立即下跌，卖出后立即上涨
        2. 错过机会：持有股票大涨但信号是 hold
        3. 止损不及时：亏损超过阈值但没有卖出信号
        4. 频繁交易：同一股票当天买卖超过 2 次
        5. 仓位过重：单只股票占比超过 30%
        """
```

---

## 5. 调度器设计

### 5.1 TradingScheduler

**位置**: `src/trading/scheduler.py`

```python
class TradingScheduler:
    """交易调度器"""

    def setup(self, engine: SimulationEngine):
        """设置定时任务"""

        # 盘中分析：交易日 9:30-11:30, 13:00-15:00，每 10 分钟
        self.scheduler.add_job(
            engine.run_analysis_cycle,
            CronTrigger(day_of_week='mon-fri', hour='9-11,13-14', minute='*/10'),
            id='sim_analysis'
        )

        # 午间报告：11:35 生成半日小结
        self.scheduler.add_job(
            engine.generate_half_day_summary,
            CronTrigger(day_of_week='mon-fri', hour=11, minute=35),
            id='sim_half_day'
        )

        # 收盘报告：15:30 生成每日报告 + 失误分析 + 策略调整
        self.scheduler.add_job(
            engine.generate_daily_report,
            CronTrigger(day_of_week='mon-fri', hour=15, minute=30),
            id='sim_daily_report'
        )

        # 策略调整：16:00 根据报告调整策略
        self.scheduler.add_job(
            engine.adjust_strategy,
            CronTrigger(day_of_week='mon-fri', hour=16, minute=0),
            id='sim_adjust'
        )
```

### 5.2 每日工作流时间线

```
09:30  开盘
  ├── 09:30  第一次分析（开盘快照）
  ├── 09:40  分析 → 交易
  ├── 09:50  分析 → 交易
  ├── ...
  ├── 11:30  上午收盘
  ├── 11:35  半日小结
  ├── 13:00  下午开盘
  ├── 13:10  分析 → 交易
  ├── ...
  ├── 14:50  最后一次分析
  ├── 15:00  收盘
  ├── 15:30  生成每日报告（盈亏/失误/策略调整）
  └── 16:00  策略调整
```

---

## 6. API 设计

### 6.1 新增端点

**位置**: `src/web/api/trading.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/trading/account` | 获取模拟账户信息 |
| POST | `/trading/account/reset` | 重置账户（重新开始） |
| GET | `/trading/positions` | 获取当前持仓 |
| GET | `/trading/trades` | 获取交易历史（支持日期筛选） |
| GET | `/trading/reports` | 获取每日报告列表 |
| GET | `/trading/reports/{date}` | 获取指定日期报告 |
| GET | `/trading/reports/{date}/mistakes` | 获取失误分析 |
| POST | `/trading/start` | 启动模拟交易 |
| POST | `/trading/stop` | 停止模拟交易 |
| GET | `/trading/status` | 获取运行状态 |

---

## 7. 前端设计

### 7.1 模拟交易仪表盘

**位置**: `frontend/src/pages/Trading.tsx`

页面结构：
- 顶部：总资产、当日盈亏、累计收益、最大回撤、胜率
- 控制栏：启动/停止/重置按钮，运行状态指示
- 持仓表格：股票、数量、成本、现价、盈亏
- 最近交易：时间、方向、股票、价格、评分
- 分析日志：时间、策略、股票、信号、执行状态

### 7.2 每日报告页面

**位置**: `frontend/src/pages/TradingReports.tsx`

页面结构：
- 日期选择器
- 今日总结：总资产、盈亏、交易次数
- 收益曲线：ECharts 折线图
- 失误分析：失误类型、具体描述
- 策略调整：调整内容、调整原因

### 7.3 状态管理

**位置**: `frontend/src/stores/trading.ts`

使用 Zustand 管理模拟交易状态。

---

## 8. 风险与边界情况

- **T+1 规则**：模拟买入当日不能卖出（复用 `CNRules.check_t_plus_1`）
- **涨跌停**：触及涨跌停时不执行交易（复用 `CNRules.check_price_limit`）
- **资金不足**：买入时检查可用资金，不足则跳过并记录
- **停牌处理**：获取不到价格时跳过分析
- **数据库并发**：使用 SQLite WAL 模式，避免锁冲突
- **手续费模拟**：默认万三佣金，可配置

---

## 9. 文件结构

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

frontend/src/pages/
└── Trading.tsx                   # 新增：模拟交易仪表盘

frontend/src/stores/
└── trading.ts                    # 新增：交易状态管理

frontend/src/services/
└── api.ts                        # 修改：新增 tradingApi

src/infra/
└── database.py                   # 修改：新增 sim 表初始化

src/main.py                       # 修改：启动时注册 TradingScheduler
```

---

## 10. 测试计划

| 测试文件 | 覆盖内容 |
|---------|---------|
| `tests/unit/test_simulated_gateway.py` | 模拟下单、资金扣减、持仓更新 |
| `tests/unit/test_simulation_engine.py` | 分析周期、信号聚合、交易执行流程 |
| `tests/unit/test_strategy_selector.py` | 市场状态判断、策略选择 |
| `tests/unit/test_mistake_analyzer.py` | 追涨杀跌检测、止损检测、频繁交易检测 |
| `tests/integration/test_trading_api.py` | API 端点集成测试 |
