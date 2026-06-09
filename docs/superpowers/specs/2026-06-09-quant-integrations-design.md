# 量化交易开源项目集成设计

## 概述

将 5 个开源量化交易项目接入 stock-hub，补全回测、实盘交易、AI 策略等能力。

**目标项目**：
- [QUANTAXIS](https://github.com/yutiansut/QUANTAXIS) — 全栈量化框架（数据/因子/回测/实盘/账户）
- [Qbot](https://github.com/UFund-Me/Qbot) — AI 量化机器人（强化学习策略）
- [easytrader](https://github.com/shidenggui/easytrader) — 券商实盘交易接口
- [ai_quant_trade](https://github.com/charliedream1/ai_quant_trade) — AI 量化策略（ML/DL 模型）
- [backtrader](https://github.com/mementum/backtrader) — 回测引擎（122 个技术指标）

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 工作台    │ │ 信号管理  │ │ 回测管理  │ │ 交易管理  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Web API (FastAPI)                         │
│  /signals  /backtest  /trade  /strategies  /data            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ResearchService  ExecutionService  AnalysisService         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Integration Layer (新增)                    │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ backtrader   │ │ quantaxis   │ │ easytrader   │           │
│  │ adapter      │ │ adapter     │ │ adapter      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐                            │
│  │ qbot         │ │ ai_quant    │                            │
│  │ adapter      │ │ adapter     │                            │
│  └─────────────┘ └─────────────┘                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   External Libraries                         │
│  backtrader  QUANTAXIS  easytrader  Qbot  ai_quant_trade    │
└─────────────────────────────────────────────────────────────┘
```

### 设计原则

1. **适配器隔离** — 外部库的变化不会直接影响核心服务层
2. **契约优先** — 所有 adapter 输出统一为 stock-hub 的 SignalV1/OrderPlan 契约
3. **渐进启用** — 每个 adapter 可通过配置独立启用/禁用
4. **pip 依赖** — 通过 pip install 引入，不拷贝源码

## Adapter 详细设计

### 1. Backtrader Adapter — 回测引擎

**位置**：`src/integrations/backtrader/`

```python
# src/integrations/backtrader/adapter.py

class BacktraderAdapter:
    """Backtrader 回测引擎适配器"""

    def run_backtest(
        self,
        strategy_name: str,
        symbols: list[str],
        start_date: str,
        end_date: str,
        initial_capital: float,
        params: dict = None,
    ) -> BacktestResult:
        """运行回测"""
        # 1. 从 DataService 获取数据
        # 2. 转换为 backtrader DataFeed
        # 3. 加载策略（内置或自定义）
        # 4. 运行 Cerebro 引擎
        # 5. 返回标准化结果
```

**集成点**：
- 替换 `src/web/api/backtest.py` 中的 TODO 实现
- 策略注册到 `ResearchService` 的策略列表
- 回测结果存入数据库

**内置策略**：
- MA 交叉、MACD、布林带、RSI（复用 backtrader 122 个指标）
- 支持用户自定义 Python 策略

**依赖**：`backtrader>=1.9.78`（零外部依赖）

### 2. QUANTAXIS Adapter — 数据层 + 账户管理

**位置**：`src/integrations/quantaxis/`

```python
# src/integrations/quantaxis/adapter.py

class QUANTAXISAdapter:
    """QUANTAXIS 适配器"""

    def __init__(self):
        self.data_bridge = QADataBridge()  # 数据桥接
        self.account = QARSAccount()        # 账户管理

    def fetch_market_data(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        frequency: str = "day",
    ) -> pd.DataFrame:
        """获取行情数据（Tick/L2/日线）"""

    def get_account_info(self) -> dict:
        """获取账户信息（QIFI 协议）"""

    def get_positions(self) -> list[dict]:
        """获取持仓"""
```

**集成点**：
- 扩展 `DataService` 的数据源
- QIFI 协议转换为 stock-hub 的 Position 模型
- 可选：Rust 高性能核心（需要编译）

**依赖**：
- `quantaxis>=2.1.0`
- MongoDB 4.0+（数据存储）
- 可选：ClickHouse（大数据量分析）

### 3. Easytrader Adapter — 实盘交易

**位置**：`src/integrations/easytrader/`

```python
# src/integrations/easytrader/adapter.py

class EasytraderAdapter:
    """Easytrader 实盘交易适配器"""

    def __init__(self, broker: str = "ths"):
        """
        broker: ths(同花顺) / yh(银河) / ht(华泰) / gj(国金)
        """
        self.trader = easytrader.use(broker)

    def connect(self, account_path: str):
        """连接券商客户端"""

    def buy(self, symbol: str, price: float, amount: int) -> dict:
        """买入"""

    def sell(self, symbol: str, price: float, amount: int) -> dict:
        """卖出"""

    def get_balance(self) -> dict:
        """查询资金"""

    def get_positions(self) -> list[dict]:
        """查询持仓"""

    def cancel_order(self, order_id: str) -> bool:
        """撤单"""
```

**集成点**：
- 扩展 `ExecutionService` 的交易网关
- 订单从 SignalBridge → EasytraderAdapter
- 实时持仓同步到 PositionManager

**依赖**：
- `easytrader>=0.16`
- `pywinauto>=0.6`（Windows GUI 自动化）
- 仅支持 Windows，需要券商客户端运行

### 4. Qbot Adapter — AI 策略

**位置**：`src/integrations/qbot/`

```python
# src/integrations/qbot/adapter.py

class QbotAdapter:
    """Qbot AI 策略适配器"""

    def __init__(self):
        self.rl_agent = None  # DQN/PPO agent

    def train_model(
        self,
        symbols: list[str],
        start_date: str,
        end_date: str,
        algorithm: str = "ppo",
    ) -> str:
        """训练 RL 模型"""

    def predict(
        self,
        symbols: list[str],
        model_id: str,
    ) -> dict[str, float]:
        """预测信号（返回权重）"""

    def create_signal(
        self,
        predictions: dict[str, float],
    ) -> Signal:
        """转换为 SignalV1 契约"""
```

**集成点**：
- 新增 SignalSource: `QBOT_RL`
- 预测结果通过 `ResearchService.create_signal()` 转为信号
- 模型管理（训练/保存/加载）

**依赖**：
- `torch>=2.0`
- `stable-baselines3>=2.0`

### 5. AI Quant Trade Adapter — ML 策略

**位置**：`src/integrations/ai_quant/`

```python
# src/integrations/ai_quant/adapter.py

class AIQuantAdapter:
    """AI Quant Trade 策略适配器"""

    def list_strategies(self) -> list[str]:
        """列出可用 ML 策略"""

    def run_strategy(
        self,
        strategy_name: str,
        symbols: list[str],
        params: dict = None,
    ) -> dict[str, float]:
        """运行 ML 策略，返回评分"""

    def create_signal(
        self,
        scores: dict[str, float],
        top_k: int = 10,
    ) -> Signal:
        """从评分创建信号"""
```

**集成点**：
- 新增 SignalSource: `AI_QUANT`
- 评分结果通过 `ResearchService.create_top_k_signal()` 转为 Top-K 信号
- 策略注册到分析策略列表

**依赖**：
- `scikit-learn>=1.3`
- `xgboost>=2.0`

## 数据流设计

### 信号流（Strategy → Signal → Order）

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Backtrader   │    │ Qbot         │    │ AI Quant     │
│ 回测产生信号  │    │ RL预测权重    │    │ ML评分       │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────┐
│              ResearchService.create_signal()          │
│              统一转换为 SignalV1 契约                   │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│              SignalBridge.process_signal()             │
│              风控检查 + 订单生成                         │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│              ExecutionService                          │
│         ┌─────────────────┴─────────────────┐        │
│         ▼                                   ▼        │
│  ┌──────────────┐                  ┌──────────────┐  │
│  │ 模拟执行      │                  │ Easytrader   │  │
│  │ (现有)        │                  │ 实盘执行      │  │
│  └──────────────┘                  └──────────────┘  │
└──────────────────────────────────────────────────────┘
```

### 数据流（外部数据 → DataService）

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ QUANTAXIS    │    │ Westock      │    │ A-share-skill│
│ MongoDB数据   │    │ 现有数据源    │    │ 策略数据      │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       ▼                   ▼                   ▼
┌──────────────────────────────────────────────────────┐
│              DataService (统一数据服务)                  │
│              标准化为 DataFrame 格式                     │
└──────────────────────────┬───────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────┐
│              ResearchService / BacktraderAdapter       │
│              因子计算 / 回测引擎消费                       │
└──────────────────────────────────────────────────────┘
```

## 契约扩展

### SignalSource 扩展

```python
class SignalSource(str, Enum):
    QLIB = "qlib"
    VNPY_ALPHA = "vnpy_alpha"
    MANUAL = "manual"
    LLM_PROPOSED = "llm_proposed"
    FINRL_X = "finrl_x"
    # 新增
    BACKTRADER = "backtrader"      # 回测产生
    QBOT_RL = "qbot_rl"            # Qbot RL预测
    AI_QUANT = "ai_quant"          # AI量化ML
    QUANTAXIS = "quantaxis"        # QUANTAXIS策略
```

### TradeGateway 新增

```python
class TradeGateway(str, Enum):
    SIMULATED = "simulated"        # 模拟执行（现有）
    EASYTRADER = "easytrader"      # Easytrader实盘
    QUANTAXIS = "quantaxis"        # QUANTAXIS实盘
```

## 前端页面

| 页面 | 功能 | 路由 |
|------|------|------|
| **回测管理** | 创建回测任务、查看结果、策略对比 | `/backtest` |
| **交易管理** | 券商连接、实盘下单、持仓查看 | `/trade` |
| **策略中心** | 策略列表、参数配置、训练状态 | `/strategies` |
| **数据源管理** | 数据源配置、同步状态 | `/data-sources` |

## 配置设计

```yaml
# config/default.yaml 扩展

integrations:
  backtrader:
    enabled: true
    strategies_path: "./strategies/backtrader"

  quantaxis:
    enabled: false  # 需要 MongoDB
    mongodb_uri: "mongodb://localhost:27017"

  easytrader:
    enabled: false  # 需要券商客户端
    broker: "ths"   # ths/yh/ht/gj

  qbot:
    enabled: true
    models_path: "./models/qbot"

  ai_quant:
    enabled: true
    strategies_path: "./strategies/ai_quant"
```

## 依赖管理

```toml
# pyproject.toml 扩展

[project.optional-dependencies]
backtrader = ["backtrader>=1.9.78"]
quantaxis = ["quantaxis>=2.1.0", "pymongo>=4.0"]
easytrader = ["easytrader>=0.16", "pywinauto>=0.6"]
qbot = ["torch>=2.0", "stable-baselines3>=2.0"]
ai-quant = ["scikit-learn>=1.3", "xgboost>=2.0"]
all-integrations = [
    "backtrader>=1.9.78",
    "quantaxis>=2.1.0", "pymongo>=4.0",
    "easytrader>=0.16", "pywinauto>=0.6",
    "torch>=2.0", "stable-baselines3>=2.0",
    "scikit-learn>=1.3", "xgboost>=2.0",
]
```

## 实施阶段

| 阶段 | 内容 | 预估工作量 |
|------|------|-----------|
| **Phase 1** | backtrader 回测引擎 + 回测管理页面 | 2-3 天 |
| **Phase 2** | easytrader 实盘交易 + 交易管理页面 | 2 天 |
| **Phase 3** | QUANTAXIS 数据层集成 | 2 天 |
| **Phase 4** | Qbot + ai_quant AI 策略集成 | 2-3 天 |
| **Phase 5** | 策略中心 + 数据源管理页面 | 1-2 天 |

## 文件结构

```
src/integrations/
├── __init__.py
├── registry.py              # 集成注册中心
├── base.py                  # 适配器基类
├── backtrader/
│   ├── __init__.py
│   ├── adapter.py           # 回测引擎适配器
│   ├── strategies.py        # 策略转换器
│   └── data_feed.py         # 数据源适配
├── quantaxis/
│   ├── __init__.py
│   ├── adapter.py           # QUANTAXIS 适配器
│   ├── data_bridge.py       # 数据桥接
│   └── account.py           # 账户协议转换
├── easytrader/
│   ├── __init__.py
│   ├── adapter.py           # 交易接口适配器
│   └── brokers.py           # 券商封装
├── qbot/
│   ├── __init__.py
│   ├── adapter.py           # Qbot 适配器
│   └── rl_strategies.py     # RL 策略封装
└── ai_quant/
    ├── __init__.py
    ├── adapter.py           # AI量化适配器
    └── ml_strategies.py     # ML 策略封装

frontend/src/pages/
├── Backtest.tsx             # 回测管理页面
├── Trade.tsx                # 交易管理页面
├── Strategies.tsx           # 策略中心页面
└── DataSources.tsx          # 数据源管理页面
```
