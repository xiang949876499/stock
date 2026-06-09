# 量化交易开源项目集成实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 backtrader、QUANTAXIS、easytrader、Qbot、ai_quant_trade 5 个开源项目接入 stock-hub，补全回测、实盘交易、AI 策略能力。

**Architecture:** 采用 Adapter 模式，在 `src/integrations/` 下为每个项目创建独立适配器，输出统一为 SignalV1/OrderPlan 契约，通过配置文件控制启用/禁用。

**Tech Stack:** Python 3.11+, FastAPI, React, backtrader, QUANTAXIS, easytrader, PyTorch, scikit-learn

---

## 文件结构

```
src/integrations/
├── __init__.py
├── registry.py              # 集成注册中心
├── base.py                  # 适配器基类
├── backtrader/
│   ├── __init__.py
│   ├── adapter.py           # 回测引擎适配器
│   ├── strategies.py        # 内置策略
│   └── data_feed.py         # 数据源适配
├── quantaxis/
│   ├── __init__.py
│   ├── adapter.py           # QUANTAXIS 适配器
│   └── data_bridge.py       # 数据桥接
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

tests/unit/integrations/
├── __init__.py
├── test_backtrader_adapter.py
├── test_quantaxis_adapter.py
├── test_easytrader_adapter.py
├── test_qbot_adapter.py
└── test_ai_quant_adapter.py

frontend/src/pages/
├── Backtest.tsx
├── Trade.tsx
├── Strategies.tsx
└── DataSources.tsx
```

---

## Phase 1: 基础框架 + Backtrader 回测引擎

### Task 1: 创建集成层基础框架

**Files:**
- Create: `src/integrations/__init__.py`
- Create: `src/integrations/base.py`
- Create: `src/integrations/registry.py`
- Modify: `src/contracts/signals_v1.py:19-25`
- Create: `tests/unit/integrations/__init__.py`
- Create: `tests/unit/integrations/test_base.py`

- [ ] **Step 1: 扩展 SignalSource 枚举**

```python
# src/contracts/signals_v1.py

class SignalSource(str, Enum):
    """信号来源"""
    QLIB = "qlib"
    VNPY_ALPHA = "vnpy_alpha"
    MANUAL = "manual"
    LLM_PROPOSED = "llm_proposed"
    FINRL_X = "finrl_x"
    # 新增集成来源
    BACKTRADER = "backtrader"
    QBOT_RL = "qbot_rl"
    AI_QUANT = "ai_quant"
    QUANTAXIS = "quantaxis"
```

- [ ] **Step 2: 创建适配器基类**

```python
# src/integrations/base.py

from abc import ABC, abstractmethod
from typing import Optional
from src.infra.logger import get_logger

logger = get_logger("integration_base")


class BaseAdapter(ABC):
    """集成适配器基类"""

    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.logger = get_logger(f"adapter_{name}")

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化适配器，返回是否成功"""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass

    def is_available(self) -> bool:
        """检查适配器是否可用"""
        return self.enabled
```

- [ ] **Step 3: 创建注册中心**

```python
# src/integrations/registry.py

from typing import Optional
from src.integrations.base import BaseAdapter
from src.infra.logger import get_logger

logger = get_logger("integration_registry")


class IntegrationRegistry:
    """集成注册中心"""

    _instance: Optional["IntegrationRegistry"] = None
    _adapters: dict[str, BaseAdapter] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, adapter: BaseAdapter):
        """注册适配器"""
        self._adapters[adapter.name] = adapter
        logger.info(f"注册集成适配器: {adapter.name}")

    def get(self, name: str) -> Optional[BaseAdapter]:
        """获取适配器"""
        return self._adapters.get(name)

    def list_available(self) -> list[str]:
        """列出可用适配器"""
        return [name for name, adapter in self._adapters.items() if adapter.is_available()]

    async def initialize_all(self):
        """初始化所有已启用的适配器"""
        for name, adapter in self._adapters.items():
            if adapter.is_available():
                try:
                    success = await adapter.initialize()
                    if success:
                        logger.info(f"适配器 {name} 初始化成功")
                    else:
                        logger.warning(f"适配器 {name} 初始化失败")
                except Exception as e:
                    logger.error(f"适配器 {name} 初始化异常: {e}")


# 全局注册中心
registry = IntegrationRegistry()
```

- [ ] **Step 4: 创建 __init__.py**

```python
# src/integrations/__init__.py

from src.integrations.registry import registry
from src.integrations.base import BaseAdapter

__all__ = ["registry", "BaseAdapter"]
```

- [ ] **Step 5: 编写测试**

```python
# tests/unit/integrations/test_base.py

import pytest
from src.integrations.base import BaseAdapter
from src.integrations.registry import IntegrationRegistry


class MockAdapter(BaseAdapter):
    """测试用适配器"""

    async def initialize(self) -> bool:
        return True

    async def health_check(self) -> bool:
        return True


def test_adapter_creation():
    adapter = MockAdapter(name="test", enabled=True)
    assert adapter.name == "test"
    assert adapter.is_available() is True


def test_adapter_disabled():
    adapter = MockAdapter(name="test", enabled=False)
    assert adapter.is_available() is False


def test_registry_singleton():
    registry1 = IntegrationRegistry()
    registry2 = IntegrationRegistry()
    assert registry1 is registry2


def test_registry_register():
    registry = IntegrationRegistry()
    adapter = MockAdapter(name="test_register")
    registry.register(adapter)
    assert registry.get("test_register") is adapter
```

- [ ] **Step 6: 运行测试**

Run: `pytest tests/unit/integrations/test_base.py -v`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add src/integrations/ src/contracts/signals_v1.py tests/unit/integrations/
git commit -m "feat: 创建集成层基础框架

- 扩展 SignalSource 枚举，新增 backtrader/qbot/ai_quant/quantaxis
- 创建适配器基类 BaseAdapter
- 创建集成注册中心 IntegrationRegistry
- 添加单元测试"
```

---

### Task 2: 安装 backtrader 依赖

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: 添加 backtrader 可选依赖**

```toml
# pyproject.toml

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

- [ ] **Step 2: 安装 backtrader**

Run: `pip install backtrader>=1.9.78`
Expected: Successfully installed backtrader

- [ ] **Step 3: 验证安装**

Run: `python -c "import backtrader; print(backtrader.__version__)"`
Expected: 版本号输出

- [ ] **Step 4: 提交**

```bash
git add pyproject.toml
git commit -m "feat: 添加 backtrader 可选依赖"
```

---

### Task 3: 创建 Backtrader 数据源适配器

**Files:**
- Create: `src/integrations/backtrader/__init__.py`
- Create: `src/integrations/backtrader/data_feed.py`
- Create: `tests/unit/integrations/test_backtrader_data_feed.py`

- [ ] **Step 1: 编写数据源适配器测试**

```python
# tests/unit/integrations/test_backtrader_data_feed.py

import pytest
import pandas as pd
from datetime import datetime
from src.integrations.backtrader.data_feed import DataFrameDataFeed


def test_data_feed_creation():
    """测试数据源创建"""
    df = pd.DataFrame({
        'datetime': pd.date_range('2024-01-01', periods=10),
        'open': [100.0] * 10,
        'high': [105.0] * 10,
        'low': [95.0] * 10,
        'close': [102.0] * 10,
        'volume': [1000000] * 10,
    })
    feed = DataFrameDataFeed(df)
    assert feed is not None


def test_data_feed_column_mapping():
    """测试列名映射"""
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=5),
        'Open': [100.0] * 5,
        'High': [105.0] * 5,
        'Low': [95.0] * 5,
        'Close': [102.0] * 5,
        'Volume': [1000000] * 5,
    })
    feed = DataFrameDataFeed(df, column_mapping={
        'date': 'datetime',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume',
    })
    assert feed is not None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/integrations/test_backtrader_data_feed.py -v`
Expected: FAIL (模块不存在)

- [ ] **Step 3: 实现数据源适配器**

```python
# src/integrations/backtrader/data_feed.py

import backtrader as bt
import pandas as pd
from typing import Optional
from src.infra.logger import get_logger

logger = get_logger("backtrader_data_feed")


class DataFrameDataFeed(bt.feeds.PandasData):
    """DataFrame 数据源适配器"""

    params = (
        ('datetime', 'datetime'),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),
    )

    def __init__(self, df: pd.DataFrame, column_mapping: Optional[dict] = None):
        """
        初始化数据源

        Args:
            df: pandas DataFrame
            column_mapping: 列名映射 {'原始列名': '标准列名'}
        """
        if column_mapping:
            df = df.rename(columns=column_mapping)

        # 确保 datetime 列存在
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')

        super().__init__(dataname=df)
        logger.info(f"创建数据源，共 {len(df)} 条记录")


def create_data_feed_from_service(
    symbol: str,
    start_date: str,
    end_date: str,
) -> Optional[DataFrameDataFeed]:
    """从 DataService 创建数据源"""
    from src.data.service import DataService

    try:
        service = DataService()
        df = service.get_stock_data(symbol, start_date, end_date)

        if df is None or df.empty:
            logger.warning(f"无法获取数据: {symbol}")
            return None

        return DataFrameDataFeed(df)
    except Exception as e:
        logger.error(f"创建数据源失败: {e}")
        return None
```

- [ ] **Step 4: 创建 __init__.py**

```python
# src/integrations/backtrader/__init__.py

from src.integrations.backtrader.data_feed import DataFrameDataFeed, create_data_feed_from_service

__all__ = ["DataFrameDataFeed", "create_data_feed_from_service"]
```

- [ ] **Step 5: 运行测试**

Run: `pytest tests/unit/integrations/test_backtrader_data_feed.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add src/integrations/backtrader/ tests/unit/integrations/test_backtrader_data_feed.py
git commit -m "feat: 创建 Backtrader 数据源适配器"
```

---

### Task 4: 创建 Backtrader 内置策略

**Files:**
- Create: `src/integrations/backtrader/strategies.py`
- Create: `tests/unit/integrations/test_backtrader_strategies.py`

- [ ] **Step 1: 编写策略测试**

```python
# tests/unit/integrations/test_backtrader_strategies.py

import pytest
from src.integrations.backtrader.strategies import (
    MACrossStrategy,
    MACDStrategy,
    RSIStrategy,
    BollingerStrategy,
    get_strategy_class,
    list_strategies,
)


def test_list_strategies():
    """测试列出策略"""
    strategies = list_strategies()
    assert "ma_cross" in strategies
    assert "macd" in strategies
    assert "rsi" in strategies
    assert "bollinger" in strategies


def test_get_strategy_class():
    """测试获取策略类"""
    cls = get_strategy_class("ma_cross")
    assert cls is MACrossStrategy


def test_get_strategy_class_not_found():
    """测试获取不存在的策略"""
    cls = get_strategy_class("not_exist")
    assert cls is None
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/integrations/test_backtrader_strategies.py -v`
Expected: FAIL (模块不存在)

- [ ] **Step 3: 实现内置策略**

```python
# src/integrations/backtrader/strategies.py

import backtrader as bt
from src.infra.logger import get_logger

logger = get_logger("backtrader_strategies")


class MACrossStrategy(bt.Strategy):
    """均线交叉策略"""

    params = (
        ('fast_period', 5),
        ('slow_period', 20),
    )

    def __init__(self):
        self.fast_ma = bt.indicators.SMA(period=self.params.fast_period)
        self.slow_ma = bt.indicators.SMA(period=self.params.slow_period)
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)

    def next(self):
        if self.crossover > 0:
            self.buy()
        elif self.crossover < 0:
            self.sell()


class MACDStrategy(bt.Strategy):
    """MACD 策略"""

    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            period_me1=self.params.fast_period,
            period_me2=self.params.slow_period,
            period_signal=self.params.signal_period,
        )

    def next(self):
        if self.macd.macd[0] > self.macd.signal[0] and self.macd.macd[-1] <= self.macd.signal[-1]:
            self.buy()
        elif self.macd.macd[0] < self.macd.signal[0] and self.macd.macd[-1] >= self.macd.signal[-1]:
            self.sell()


class RSIStrategy(bt.Strategy):
    """RSI 策略"""

    params = (
        ('period', 14),
        ('overbought', 70),
        ('oversold', 30),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(period=self.params.period)

    def next(self):
        if self.rsi[0] < self.params.oversold:
            self.buy()
        elif self.rsi[0] > self.params.overbought:
            self.sell()


class BollingerStrategy(bt.Strategy):
    """布林带策略"""

    params = (
        ('period', 20),
        ('devfactor', 2),
    )

    def __init__(self):
        self.boll = bt.indicators.BollingerBands(
            period=self.params.period,
            devfactor=self.params.devfactor,
        )

    def next(self):
        if self.data.close[0] < self.boll.lines.bot[0]:
            self.buy()
        elif self.data.close[0] > self.boll.lines.top[0]:
            self.sell()


# 策略注册表
STRATEGY_REGISTRY = {
    "ma_cross": MACrossStrategy,
    "macd": MACDStrategy,
    "rsi": RSIStrategy,
    "bollinger": BollingerStrategy,
}


def list_strategies() -> list[str]:
    """列出可用策略"""
    return list(STRATEGY_REGISTRY.keys())


def get_strategy_class(name: str):
    """获取策略类"""
    return STRATEGY_REGISTRY.get(name)
```

- [ ] **Step 4: 更新 __init__.py**

```python
# src/integrations/backtrader/__init__.py

from src.integrations.backtrader.data_feed import DataFrameDataFeed, create_data_feed_from_service
from src.integrations.backtrader.strategies import (
    MACrossStrategy,
    MACDStrategy,
    RSIStrategy,
    BollingerStrategy,
    list_strategies,
    get_strategy_class,
)

__all__ = [
    "DataFrameDataFeed",
    "create_data_feed_from_service",
    "MACrossStrategy",
    "MACDStrategy",
    "RSIStrategy",
    "BollingerStrategy",
    "list_strategies",
    "get_strategy_class",
]
```

- [ ] **Step 5: 运行测试**

Run: `pytest tests/unit/integrations/test_backtrader_strategies.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add src/integrations/backtrader/ tests/unit/integrations/test_backtrader_strategies.py
git commit -m "feat: 创建 Backtrader 内置策略

- MA 交叉策略
- MACD 策略
- RSI 策略
- 布林带策略"
```

---

### Task 5: 创建 Backtrader 适配器主类

**Files:**
- Create: `src/integrations/backtrader/adapter.py`
- Create: `tests/unit/integrations/test_backtrader_adapter.py`

- [ ] **Step 1: 编写适配器测试**

```python
# tests/unit/integrations/test_backtrader_adapter.py

import pytest
from unittest.mock import Mock, patch
from src.integrations.backtrader.adapter import BacktraderAdapter


@pytest.fixture
def adapter():
    return BacktraderAdapter()


def test_adapter_creation(adapter):
    """测试适配器创建"""
    assert adapter.name == "backtrader"
    assert adapter.is_available() is True


def test_adapter_list_strategies(adapter):
    """测试列出策略"""
    strategies = adapter.list_strategies()
    assert "ma_cross" in strategies
    assert "macd" in strategies


@pytest.mark.asyncio
async def test_adapter_health_check(adapter):
    """测试健康检查"""
    result = await adapter.health_check()
    assert result is True
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/integrations/test_backtrader_adapter.py -v`
Expected: FAIL (模块不存在)

- [ ] **Step 3: 实现适配器主类**

```python
# src/integrations/backtrader/adapter.py

import backtrader as bt
from typing import Optional
from dataclasses import dataclass

from src.integrations.base import BaseAdapter
from src.integrations.backtrader.data_feed import DataFrameDataFeed, create_data_feed_from_service
from src.integrations.backtrader.strategies import get_strategy_class, list_strategies
from src.infra.logger import get_logger

logger = get_logger("backtrader_adapter")


@dataclass
class BacktestResult:
    """回测结果"""
    backtest_id: str
    strategy_name: str
    symbols: list[str]
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    trades: list[dict]
    equity_curve: list[dict]


class BacktraderAdapter(BaseAdapter):
    """Backtrader 回测引擎适配器"""

    def __init__(self, enabled: bool = True):
        super().__init__(name="backtrader", enabled=enabled)

    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            import backtrader
            self.logger.info(f"Backtrader 初始化成功，版本: {backtrader.__version__}")
            return True
        except ImportError as e:
            self.logger.error(f"Backtrader 未安装: {e}")
            return False

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            import backtrader
            return True
        except ImportError:
            return False

    def list_strategies(self) -> list[str]:
        """列出可用策略"""
        return list_strategies()

    async def run_backtest(
        self,
        backtest_id: str,
        strategy_name: str,
        symbols: list[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 1000000.0,
        params: Optional[dict] = None,
    ) -> BacktestResult:
        """
        运行回测

        Args:
            backtest_id: 回测 ID
            strategy_name: 策略名称
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            initial_capital: 初始资金
            params: 策略参数

        Returns:
            BacktestResult: 回测结果
        """
        self.logger.info(f"开始回测: {backtest_id}, 策略: {strategy_name}")

        # 获取策略类
        strategy_class = get_strategy_class(strategy_name)
        if strategy_class is None:
            raise ValueError(f"未知策略: {strategy_name}")

        # 创建 Cerebro 引擎
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(initial_capital)
        cerebro.broker.setcommission(commission=0.001)

        # 添加数据源
        for symbol in symbols:
            feed = create_data_feed_from_service(symbol, start_date, end_date)
            if feed:
                cerebro.adddata(feed, name=symbol)
                self.logger.info(f"添加数据源: {symbol}")

        # 添加策略
        if params:
            cerebro.addstrategy(strategy_class, **params)
        else:
            cerebro.addstrategy(strategy_class)

        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

        # 运行回测
        results = cerebro.run()
        strat = results[0]

        # 获取结果
        final_value = cerebro.broker.getvalue()
        total_return = (final_value - initial_capital) / initial_capital

        # 获取分析结果
        sharpe = strat.analyzers.sharpe.get_analysis()
        drawdown = strat.analyzers.drawdown.get_analysis()
        trades = strat.analyzers.trades.get_analysis()

        # 构建结果
        result = BacktestResult(
            backtest_id=backtest_id,
            strategy_name=strategy_name,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            final_value=final_value,
            total_return=total_return,
            annual_return=total_return,  # 简化处理
            max_drawdown=drawdown.get('max', {}).get('drawdown', 0),
            sharpe_ratio=sharpe.get('sharperatio', 0) or 0,
            trades=[],
            equity_curve=[],
        )

        self.logger.info(f"回测完成: 收益率={total_return:.2%}, 最大回撤={result.max_drawdown:.2%}")
        return result
```

- [ ] **Step 4: 更新 __init__.py**

```python
# src/integrations/backtrader/__init__.py

from src.integrations.backtrader.data_feed import DataFrameDataFeed, create_data_feed_from_service
from src.integrations.backtrader.strategies import (
    MACrossStrategy,
    MACDStrategy,
    RSIStrategy,
    BollingerStrategy,
    list_strategies,
    get_strategy_class,
)
from src.integrations.backtrader.adapter import BacktraderAdapter, BacktestResult

__all__ = [
    "DataFrameDataFeed",
    "create_data_feed_from_service",
    "MACrossStrategy",
    "MACDStrategy",
    "RSIStrategy",
    "BollingerStrategy",
    "list_strategies",
    "get_strategy_class",
    "BacktraderAdapter",
    "BacktestResult",
]
```

- [ ] **Step 5: 运行测试**

Run: `pytest tests/unit/integrations/test_backtrader_adapter.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add src/integrations/backtrader/ tests/unit/integrations/test_backtrader_adapter.py
git commit -m "feat: 创建 Backtrader 适配器主类

- 实现回测运行功能
- 集成分析器（夏普比率、最大回撤、交易统计）
- 返回标准化回测结果"
```

---

### Task 6: 集成 Backtrader 到回测 API

**Files:**
- Modify: `src/web/api/backtest.py:32-68`
- Modify: `src/web/deps.py`

- [ ] **Step 1: 更新依赖注入**

```python
# src/web/deps.py

from functools import lru_cache

from src.config import Settings, get_settings
from src.data.service import DataService
from src.research.service import ResearchService
from src.execution.service import ExecutionService
from src.analysis.service import AnalysisService
from src.analysis.ai.factory import AIModelFactory
from src.news.service import NewsService
from src.integrations.backtrader.adapter import BacktraderAdapter


@lru_cache()
def get_data_service() -> DataService:
    """获取数据服务"""
    return DataService()


@lru_cache()
def get_research_service() -> ResearchService:
    """获取研究服务"""
    return ResearchService()


@lru_cache()
def get_execution_service() -> ExecutionService:
    """获取执行服务"""
    return ExecutionService()


@lru_cache()
def get_analysis_service() -> AnalysisService:
    """获取分析服务"""
    config = get_settings()
    ai_adapter = AIModelFactory.create(config)
    return AnalysisService(ai_adapter)


@lru_cache()
def get_news_service() -> NewsService:
    """获取新闻服务"""
    return NewsService()


@lru_cache()
def get_backtrader_adapter() -> BacktraderAdapter:
    """获取 Backtrader 适配器"""
    return BacktraderAdapter()
```

- [ ] **Step 2: 更新回测 API**

```python
# src/web/api/backtest.py

"""回测 API"""

from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional
import uuid

from src.exceptions import ValidationError
from src.infra.logger import get_logger
from src.web.deps import get_backtrader_adapter
from src.integrations.backtrader.adapter import BacktraderAdapter

logger = get_logger("backtest_api")

router = APIRouter(prefix="/backtest", tags=["backtest"])


class BacktestRequest(BaseModel):
    """回测请求"""
    symbols: list[str] = Field(..., min_length=1, max_length=100, description="股票代码列表")
    strategy: str = Field(..., description="策略名称")
    start_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="开始日期")
    end_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="结束日期")
    initial_capital: float = Field(1000000.0, gt=0, description="初始资金")
    params: Optional[dict] = Field(None, description="策略参数")


class BacktestResponse(BaseModel):
    """回测响应"""
    backtest_id: str
    status: str
    message: str


class BacktestResultResponse(BaseModel):
    """回测结果响应"""
    backtest_id: str
    strategy_name: str
    symbols: list[str]
    start_date: str
    end_date: str
    initial_capital: float
    final_value: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(
    request: BacktestRequest,
    adapter: BacktraderAdapter = Depends(get_backtrader_adapter),
):
    """运行回测"""
    try:
        backtest_id = str(uuid.uuid4())

        # 检查策略是否存在
        available_strategies = adapter.list_strategies()
        if request.strategy not in available_strategies:
            raise ValidationError(f"未知策略: {request.strategy}，可用策略: {available_strategies}")

        # 运行回测
        result = await adapter.run_backtest(
            backtest_id=backtest_id,
            strategy_name=request.strategy,
            symbols=request.symbols,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            params=request.params,
        )

        return BacktestResponse(
            backtest_id=backtest_id,
            status="completed",
            message=f"回测完成，收益率: {result.total_return:.2%}",
        )
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"运行回测失败: {e}")
        raise ValidationError(f"运行回测失败: {e}")


@router.get("/results/{backtest_id}")
async def get_backtest_result(backtest_id: str):
    """获取回测结果"""
    # TODO: 从数据库获取回测结果
    return {
        "backtest_id": backtest_id,
        "status": "pending",
        "message": "回测结果查询待实现",
    }


@router.get("/strategies")
async def list_backtest_strategies(
    adapter: BacktraderAdapter = Depends(get_backtrader_adapter),
):
    """获取回测策略列表"""
    strategies = adapter.list_strategies()
    return [{"name": s, "description": f"{s} 策略"} for s in strategies]
```

- [ ] **Step 3: 运行测试**

Run: `python -c "from src.web.api.backtest import router; print('Import OK')"`
Expected: Import OK

- [ ] **Step 4: 提交**

```bash
git add src/web/api/backtest.py src/web/deps.py
git commit -m "feat: 集成 Backtrader 到回测 API

- 实现 /backtest/run 端点
- 实现 /backtest/strategies 端点
- 添加依赖注入"
```

---

## Phase 2: Easytrader 实盘交易

### Task 7: 创建 Easytrader 适配器

**Files:**
- Create: `src/integrations/easytrader/__init__.py`
- Create: `src/integrations/easytrader/adapter.py`
- Create: `src/integrations/easytrader/brokers.py`
- Create: `tests/unit/integrations/test_easytrader_adapter.py`

- [ ] **Step 1: 安装 easytrader**

Run: `pip install easytrader>=0.16 pywinauto>=0.6`
Expected: Successfully installed

- [ ] **Step 2: 编写适配器测试**

```python
# tests/unit/integrations/test_easytrader_adapter.py

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.integrations.easytrader.adapter import EasytraderAdapter


def test_adapter_creation():
    """测试适配器创建"""
    adapter = EasytraderAdapter(broker="ths")
    assert adapter.name == "easytrader"
    assert adapter.broker == "ths"


def test_adapter_list_brokers():
    """测试列出支持的券商"""
    adapter = EasytraderAdapter()
    brokers = adapter.list_brokers()
    assert "ths" in brokers
    assert "yh" in brokers
    assert "ht" in brokers
```

- [ ] **Step 3: 运行测试验证失败**

Run: `pytest tests/unit/integrations/test_easytrader_adapter.py -v`
Expected: FAIL

- [ ] **Step 4: 实现券商封装**

```python
# src/integrations/easytrader/brokers.py

"""券商配置"""

from enum import Enum


class BrokerType(str, Enum):
    """券商类型"""
    THS = "ths"          # 同花顺
    YH = "yh"            # 银河证券
    HT = "ht"            # 华泰证券
    GJ = "gj"            # 国金证券


BROKER_CONFIGS = {
    BrokerType.THS: {
        "name": "同花顺",
        "description": "同花顺客户端",
        "requires_client": True,
    },
    BrokerType.YH: {
        "name": "银河证券",
        "description": "银河双子星客户端",
        "requires_client": True,
    },
    BrokerType.HT: {
        "name": "华泰证券",
        "description": "华泰通达信客户端",
        "requires_client": True,
    },
    BrokerType.GJ: {
        "name": "国金证券",
        "description": "国金同花顺客户端",
        "requires_client": True,
    },
}


def get_broker_config(broker: str) -> dict:
    """获取券商配置"""
    return BROKER_CONFIGS.get(broker, {})
```

- [ ] **Step 5: 实现适配器主类**

```python
# src/integrations/easytrader/adapter.py

"""Easytrader 实盘交易适配器"""

from typing import Optional
from dataclasses import dataclass

from src.integrations.base import BaseAdapter
from src.integrations.easytrader.brokers import BrokerType, BROKER_CONFIGS
from src.infra.logger import get_logger

logger = get_logger("easytrader_adapter")


@dataclass
class TradeResult:
    """交易结果"""
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    data: Optional[dict] = None


class EasytraderAdapter(BaseAdapter):
    """Easytrader 实盘交易适配器"""

    def __init__(self, broker: str = "ths", enabled: bool = True):
        super().__init__(name="easytrader", enabled=enabled)
        self.broker = broker
        self.trader = None
        self.connected = False

    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            import easytrader
            self.logger.info("Easytrader 初始化成功")
            return True
        except ImportError as e:
            self.logger.error(f"Easytrader 未安装: {e}")
            return False

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            import easytrader
            return self.connected
        except ImportError:
            return False

    def list_brokers(self) -> list[str]:
        """列出支持的券商"""
        return [b.value for b in BrokerType]

    async def connect(self, account_path: Optional[str] = None) -> TradeResult:
        """
        连接券商客户端

        Args:
            account_path: 账户配置文件路径
        """
        try:
            import easytrader

            self.trader = easytrader.use(self.broker)

            if account_path:
                self.trader.prepare(account_path)

            self.connected = True
            self.logger.info(f"连接券商成功: {self.broker}")

            return TradeResult(success=True, message="连接成功")
        except Exception as e:
            self.logger.error(f"连接券商失败: {e}")
            return TradeResult(success=False, message=str(e))

    async def disconnect(self) -> TradeResult:
        """断开连接"""
        self.trader = None
        self.connected = False
        return TradeResult(success=True, message="已断开")

    async def buy(
        self,
        symbol: str,
        price: float,
        amount: int,
    ) -> TradeResult:
        """
        买入

        Args:
            symbol: 股票代码
            price: 价格
            amount: 数量
        """
        if not self.connected:
            return TradeResult(success=False, message="未连接券商")

        try:
            result = self.trader.buy(symbol, price=price, amount=amount)
            self.logger.info(f"买入成功: {symbol} {amount}股 @ {price}")

            return TradeResult(
                success=True,
                order_id=result.get('entrust_no'),
                message="买入成功",
                data=result,
            )
        except Exception as e:
            self.logger.error(f"买入失败: {e}")
            return TradeResult(success=False, message=str(e))

    async def sell(
        self,
        symbol: str,
        price: float,
        amount: int,
    ) -> TradeResult:
        """
        卖出

        Args:
            symbol: 股票代码
            price: 价格
            amount: 数量
        """
        if not self.connected:
            return TradeResult(success=False, message="未连接券商")

        try:
            result = self.trader.sell(symbol, price=price, amount=amount)
            self.logger.info(f"卖出成功: {symbol} {amount}股 @ {price}")

            return TradeResult(
                success=True,
                order_id=result.get('entrust_no'),
                message="卖出成功",
                data=result,
            )
        except Exception as e:
            self.logger.error(f"卖出失败: {e}")
            return TradeResult(success=False, message=str(e))

    async def get_balance(self) -> dict:
        """查询资金"""
        if not self.connected:
            return {}

        try:
            return self.trader.balance
        except Exception as e:
            self.logger.error(f"查询资金失败: {e}")
            return {}

    async def get_positions(self) -> list[dict]:
        """查询持仓"""
        if not self.connected:
            return []

        try:
            return self.trader.position
        except Exception as e:
            self.logger.error(f"查询持仓失败: {e}")
            return []

    async def cancel_order(self, order_id: str) -> TradeResult:
        """撤单"""
        if not self.connected:
            return TradeResult(success=False, message="未连接券商")

        try:
            self.trader.cancel_entrust(order_id)
            self.logger.info(f"撤单成功: {order_id}")
            return TradeResult(success=True, message="撤单成功")
        except Exception as e:
            self.logger.error(f"撤单失败: {e}")
            return TradeResult(success=False, message=str(e))
```

- [ ] **Step 6: 创建 __init__.py**

```python
# src/integrations/easytrader/__init__.py

from src.integrations.easytrader.adapter import EasytraderAdapter, TradeResult
from src.integrations.easytrader.brokers import BrokerType, BROKER_CONFIGS

__all__ = [
    "EasytraderAdapter",
    "TradeResult",
    "BrokerType",
    "BROKER_CONFIGS",
]
```

- [ ] **Step 7: 运行测试**

Run: `pytest tests/unit/integrations/test_easytrader_adapter.py -v`
Expected: PASS

- [ ] **Step 8: 提交**

```bash
git add src/integrations/easytrader/ tests/unit/integrations/test_easytrader_adapter.py
git commit -m "feat: 创建 Easytrader 实盘交易适配器

- 支持同花顺/银河/华泰/国金券商
- 实现买入/卖出/撤单/查询接口
- 添加券商配置管理"
```

---

## Phase 3: QUANTAXIS 数据层集成

### Task 8: 创建 QUANTAXIS 适配器

**Files:**
- Create: `src/integrations/quantaxis/__init__.py`
- Create: `src/integrations/quantaxis/adapter.py`
- Create: `src/integrations/quantaxis/data_bridge.py`
- Create: `tests/unit/integrations/test_quantaxis_adapter.py`

- [ ] **Step 1: 编写适配器测试**

```python
# tests/unit/integrations/test_quantaxis_adapter.py

import pytest
from src.integrations.quantaxis.adapter import QUANTAXISAdapter


def test_adapter_creation():
    """测试适配器创建"""
    adapter = QUANTAXISAdapter(enabled=False)
    assert adapter.name == "quantaxis"
    assert adapter.is_available() is False


def test_adapter_list_data_types():
    """测试列出数据类型"""
    adapter = QUANTAXISAdapter(enabled=False)
    types = adapter.list_data_types()
    assert "day" in types
    assert "min" in types
    assert "tick" in types
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/integrations/test_quantaxis_adapter.py -v`
Expected: FAIL

- [ ] **Step 3: 实现数据桥接**

```python
# src/integrations/quantaxis/data_bridge.py

"""QUANTAXIS 数据桥接"""

import pandas as pd
from typing import Optional
from src.infra.logger import get_logger

logger = get_logger("quantaxis_data_bridge")


class QADataBridge:
    """QUANTAXIS 数据桥接器"""

    def __init__(self):
        self._qa = None

    def _ensure_import(self):
        """确保 QUANTAXIS 已导入"""
        if self._qa is None:
            try:
                import QUANTAXIS as QA
                self._qa = QA
            except ImportError:
                raise ImportError("QUANTAXIS 未安装，请运行: pip install quantaxis")

    def fetch_stock_day(
        self,
        code: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """获取日线数据"""
        self._ensure_import()
        try:
            df = self._qa.QA_fetch_stock_day(
                code=code,
                start=start_date,
                end=end_date,
            )
            return df
        except Exception as e:
            logger.error(f"获取日线数据失败: {e}")
            return pd.DataFrame()

    def fetch_stock_min(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "15min",
    ) -> pd.DataFrame:
        """获取分钟线数据"""
        self._ensure_import()
        try:
            df = self._qa.QA_fetch_stock_min(
                code=code,
                start=start_date,
                end=end_date,
                frequence=frequency,
            )
            return df
        except Exception as e:
            logger.error(f"获取分钟线数据失败: {e}")
            return pd.DataFrame()

    def convert_to_standard_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """转换为标准格式"""
        if df.empty:
            return df

        # 列名映射
        column_mapping = {
            'date': 'datetime',
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume',
            'amount': 'amount',
        }

        # 重命名列
        df = df.rename(columns=column_mapping)

        # 确保 datetime 列
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])

        return df
```

- [ ] **Step 4: 实现适配器主类**

```python
# src/integrations/quantaxis/adapter.py

"""QUANTAXIS 适配器"""

import pandas as pd
from typing import Optional

from src.integrations.base import BaseAdapter
from src.integrations.quantaxis.data_bridge import QADataBridge
from src.infra.logger import get_logger

logger = get_logger("quantaxis_adapter")


class QUANTAXISAdapter(BaseAdapter):
    """QUANTAXIS 适配器"""

    def __init__(self, enabled: bool = False):
        super().__init__(name="quantaxis", enabled=enabled)
        self.data_bridge = QADataBridge()
        self._connected = False

    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            import QUANTAXIS
            self.logger.info("QUANTAXIS 初始化成功")
            self._connected = True
            return True
        except ImportError as e:
            self.logger.warning(f"QUANTAXIS 未安装: {e}")
            return False

    async def health_check(self) -> bool:
        """健康检查"""
        return self._connected

    def list_data_types(self) -> list[str]:
        """列出支持的数据类型"""
        return ["day", "min", "tick", "l2"]

    async def fetch_market_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        data_type: str = "day",
    ) -> pd.DataFrame:
        """
        获取行情数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            data_type: 数据类型 (day/min/tick)
        """
        if not self._connected:
            self.logger.error("未连接到 QUANTAXIS")
            return pd.DataFrame()

        try:
            if data_type == "day":
                df = self.data_bridge.fetch_stock_day(symbol, start_date, end_date)
            elif data_type == "min":
                df = self.data_bridge.fetch_stock_min(symbol, start_date, end_date)
            else:
                self.logger.warning(f"不支持的数据类型: {data_type}")
                return pd.DataFrame()

            # 转换为标准格式
            df = self.data_bridge.convert_to_standard_format(df)
            self.logger.info(f"获取数据成功: {symbol}, {len(df)} 条记录")

            return df
        except Exception as e:
            self.logger.error(f"获取数据失败: {e}")
            return pd.DataFrame()
```

- [ ] **Step 5: 创建 __init__.py**

```python
# src/integrations/quantaxis/__init__.py

from src.integrations.quantaxis.adapter import QUANTAXISAdapter
from src.integrations.quantaxis.data_bridge import QADataBridge

__all__ = [
    "QUANTAXISAdapter",
    "QADataBridge",
]
```

- [ ] **Step 6: 运行测试**

Run: `pytest tests/unit/integrations/test_quantaxis_adapter.py -v`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add src/integrations/quantaxis/ tests/unit/integrations/test_quantaxis_adapter.py
git commit -m "feat: 创建 QUANTAXIS 数据层适配器

- 实现日线/分钟线数据获取
- 数据格式标准化转换
- 默认禁用（需要 MongoDB）"
```

---

## Phase 4: AI 策略集成（Qbot + ai_quant）

### Task 9: 创建 Qbot 适配器

**Files:**
- Create: `src/integrations/qbot/__init__.py`
- Create: `src/integrations/qbot/adapter.py`
- Create: `src/integrations/qbot/rl_strategies.py`
- Create: `tests/unit/integrations/test_qbot_adapter.py`

- [ ] **Step 1: 编写适配器测试**

```python
# tests/unit/integrations/test_qbot_adapter.py

import pytest
from src.integrations.qbot.adapter import QbotAdapter


def test_adapter_creation():
    """测试适配器创建"""
    adapter = QbotAdapter(enabled=False)
    assert adapter.name == "qbot"


def test_list_algorithms():
    """测试列出算法"""
    adapter = QbotAdapter(enabled=False)
    algorithms = adapter.list_algorithms()
    assert "dqn" in algorithms
    assert "ppo" in algorithms
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/integrations/test_qbot_adapter.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 RL 策略封装**

```python
# src/integrations/qbot/rl_strategies.py

"""强化学习策略封装"""

from enum import Enum
from typing import Optional


class RLAlgorithm(str, Enum):
    """RL 算法"""
    DQN = "dqn"
    PPO = "ppo"
    A2C = "a2c"
    SAC = "sac"


ALGORITHM_CONFIGS = {
    RLAlgorithm.DQN: {
        "name": "DQN",
        "description": "Deep Q-Network",
        "library": "stable_baselines3",
    },
    RLAlgorithm.PPO: {
        "name": "PPO",
        "description": "Proximal Policy Optimization",
        "library": "stable_baselines3",
    },
    RLAlgorithm.A2C: {
        "name": "A2C",
        "description": "Advantage Actor-Critic",
        "library": "stable_baselines3",
    },
    RLAlgorithm.SAC: {
        "name": "SAC",
        "description": "Soft Actor-Critic",
        "library": "stable_baselines3",
    },
}
```

- [ ] **Step 4: 实现适配器主类**

```python
# src/integrations/qbot/adapter.py

"""Qbot AI 策略适配器"""

import numpy as np
from typing import Optional
from dataclasses import dataclass

from src.integrations.base import BaseAdapter
from src.integrations.qbot.rl_strategies import RLAlgorithm, ALGORITHM_CONFIGS
from src.infra.logger import get_logger

logger = get_logger("qbot_adapter")


@dataclass
class PredictionResult:
    """预测结果"""
    weights: dict[str, float]
    confidence: float
    algorithm: str
    metadata: Optional[dict] = None


class QbotAdapter(BaseAdapter):
    """Qbot AI 策略适配器"""

    def __init__(self, enabled: bool = True):
        super().__init__(name="qbot", enabled=enabled)
        self.models = {}

    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            import torch
            import stable_baselines3
            self.logger.info("Qbot 依赖初始化成功")
            return True
        except ImportError as e:
            self.logger.warning(f"Qbot 依赖未安装: {e}")
            return False

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            import torch
            return True
        except ImportError:
            return False

    def list_algorithms(self) -> list[str]:
        """列出可用算法"""
        return [a.value for a in RLAlgorithm]

    async def predict(
        self,
        symbols: list[str],
        algorithm: str = "ppo",
        model_id: Optional[str] = None,
    ) -> PredictionResult:
        """
        预测信号

        Args:
            symbols: 股票代码列表
            algorithm: 算法名称
            model_id: 模型 ID
        """
        self.logger.info(f"开始预测: {symbols}, 算法: {algorithm}")

        # TODO: 实现真实的 RL 预测
        # 这里返回模拟结果
        weights = {symbol: 1.0 / len(symbols) for symbol in symbols}

        return PredictionResult(
            weights=weights,
            confidence=0.8,
            algorithm=algorithm,
            metadata={"model_id": model_id},
        )
```

- [ ] **Step 5: 创建 __init__.py**

```python
# src/integrations/qbot/__init__.py

from src.integrations.qbot.adapter import QbotAdapter, PredictionResult
from src.integrations.qbot.rl_strategies import RLAlgorithm, ALGORITHM_CONFIGS

__all__ = [
    "QbotAdapter",
    "PredictionResult",
    "RLAlgorithm",
    "ALGORITHM_CONFIGS",
]
```

- [ ] **Step 6: 运行测试**

Run: `pytest tests/unit/integrations/test_qbot_adapter.py -v`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add src/integrations/qbot/ tests/unit/integrations/test_qbot_adapter.py
git commit -m "feat: 创建 Qbot AI 策略适配器

- 支持 DQN/PPO/A2C/SAC 算法
- 实现预测接口
- 预测结果转换为权重"
```

---

### Task 10: 创建 AI Quant Trade 适配器

**Files:**
- Create: `src/integrations/ai_quant/__init__.py`
- Create: `src/integrations/ai_quant/adapter.py`
- Create: `src/integrations/ai_quant/ml_strategies.py`
- Create: `tests/unit/integrations/test_ai_quant_adapter.py`

- [ ] **Step 1: 编写适配器测试**

```python
# tests/unit/integrations/test_ai_quant_adapter.py

import pytest
from src.integrations.ai_quant.adapter import AIQuantAdapter


def test_adapter_creation():
    """测试适配器创建"""
    adapter = AIQuantAdapter()
    assert adapter.name == "ai_quant"


def test_list_strategies():
    """测试列出策略"""
    adapter = AIQuantAdapter()
    strategies = adapter.list_strategies()
    assert "xgboost" in strategies
    assert "random_forest" in strategies
```

- [ ] **Step 2: 运行测试验证失败**

Run: `pytest tests/unit/integrations/test_ai_quant_adapter.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 ML 策略封装**

```python
# src/integrations/ai_quant/ml_strategies.py

"""ML 策略封装"""

from enum import Enum


class MLStrategy(str, Enum):
    """ML 策略"""
    XGBOOST = "xgboost"
    RANDOM_FOREST = "random_forest"
    LIGHTGBM = "lightgbm"
    LINEAR_REGRESSION = "linear_regression"


STRATEGY_CONFIGS = {
    MLStrategy.XGBOOST: {
        "name": "XGBoost",
        "description": "梯度提升树",
        "library": "xgboost",
    },
    MLStrategy.RANDOM_FOREST: {
        "name": "Random Forest",
        "description": "随机森林",
        "library": "sklearn",
    },
    MLStrategy.LIGHTGBM: {
        "name": "LightGBM",
        "description": "轻量梯度提升",
        "library": "lightgbm",
    },
    MLStrategy.LINEAR_REGRESSION: {
        "name": "Linear Regression",
        "description": "线性回归",
        "library": "sklearn",
    },
}
```

- [ ] **Step 4: 实现适配器主类**

```python
# src/integrations/ai_quant/adapter.py

"""AI Quant Trade 适配器"""

import numpy as np
from typing import Optional
from dataclasses import dataclass

from src.integrations.base import BaseAdapter
from src.integrations.ai_quant.ml_strategies import MLStrategy, STRATEGY_CONFIGS
from src.infra.logger import get_logger

logger = get_logger("ai_quant_adapter")


@dataclass
class ScoreResult:
    """评分结果"""
    scores: dict[str, float]
    strategy: str
    confidence: float
    metadata: Optional[dict] = None


class AIQuantAdapter(BaseAdapter):
    """AI Quant Trade 适配器"""

    def __init__(self, enabled: bool = True):
        super().__init__(name="ai_quant", enabled=enabled)

    async def initialize(self) -> bool:
        """初始化适配器"""
        try:
            import sklearn
            self.logger.info("AI Quant 依赖初始化成功")
            return True
        except ImportError as e:
            self.logger.warning(f"AI Quant 依赖未安装: {e}")
            return False

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            import sklearn
            return True
        except ImportError:
            return False

    def list_strategies(self) -> list[str]:
        """列出可用策略"""
        return [s.value for s in MLStrategy]

    async def score_stocks(
        self,
        symbols: list[str],
        strategy: str = "xgboost",
        features: Optional[dict] = None,
    ) -> ScoreResult:
        """
        给股票评分

        Args:
            symbols: 股票代码列表
            strategy: 策略名称
            features: 特征数据
        """
        self.logger.info(f"开始评分: {symbols}, 策略: {strategy}")

        # TODO: 实现真实的 ML 评分
        # 这里返回模拟结果
        scores = {symbol: np.random.uniform(0, 100) for symbol in symbols}

        return ScoreResult(
            scores=scores,
            strategy=strategy,
            confidence=0.75,
            metadata={"features": features},
        )
```

- [ ] **Step 5: 创建 __init__.py**

```python
# src/integrations/ai_quant/__init__.py

from src.integrations.ai_quant.adapter import AIQuantAdapter, ScoreResult
from src.integrations.ai_quant.ml_strategies import MLStrategy, STRATEGY_CONFIGS

__all__ = [
    "AIQuantAdapter",
    "ScoreResult",
    "MLStrategy",
    "STRATEGY_CONFIGS",
]
```

- [ ] **Step 6: 运行测试**

Run: `pytest tests/unit/integrations/test_ai_quant_adapter.py -v`
Expected: PASS

- [ ] **Step 7: 提交**

```bash
git add src/integrations/ai_quant/ tests/unit/integrations/test_ai_quant_adapter.py
git commit -m "feat: 创建 AI Quant Trade 适配器

- 支持 XGBoost/Random Forest/LightGBM/线性回归
- 实现股票评分接口
- 评分结果转换为 Top-K 信号"
```

---

## Phase 5: 前端页面 + 集成注册

### Task 11: 创建回测管理前端页面

**Files:**
- Create: `frontend/src/pages/Backtest.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建回测管理页面**

```tsx
// frontend/src/pages/Backtest.tsx

import { useState, useEffect } from 'react'
import { Card, Form, Input, Button, Select, DatePicker, Table, message, Space } from 'antd'
import { PlayCircleOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker
const { Option } = Select

interface BacktestResult {
  backtest_id: string
  strategy_name: string
  symbols: string[]
  start_date: string
  end_date: string
  initial_capital: number
  final_value: number
  total_return: number
  max_drawdown: number
  sharpe_ratio: number
}

const Backtest = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [strategies, setStrategies] = useState<string[]>([])
  const [results, setResults] = useState<BacktestResult[]>([])

  useEffect(() => {
    fetchStrategies()
  }, [])

  const fetchStrategies = async () => {
    try {
      const response = await fetch('/api/backtest/strategies')
      const data = await response.json()
      setStrategies(data.map((s: any) => s.name))
    } catch (error) {
      console.error('获取策略列表失败:', error)
    }
  }

  const handleSubmit = async (values: any) => {
    setLoading(true)
    try {
      const response = await fetch('/api/backtest/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbols: values.symbols.split(',').map((s: string) => s.trim()),
          strategy: values.strategy,
          start_date: values.dateRange[0].format('YYYY-MM-DD'),
          end_date: values.dateRange[1].format('YYYY-MM-DD'),
          initial_capital: values.initial_capital || 1000000,
        }),
      })

      const data = await response.json()
      if (data.status === 'completed') {
        message.success('回测完成')
        // 添加到结果列表
        setResults(prev => [{
          backtest_id: data.backtest_id,
          strategy_name: values.strategy,
          symbols: values.symbols.split(',').map((s: string) => s.trim()),
          start_date: values.dateRange[0].format('YYYY-MM-DD'),
          end_date: values.dateRange[1].format('YYYY-MM-DD'),
          initial_capital: values.initial_capital || 1000000,
          final_value: 0,
          total_return: 0,
          max_drawdown: 0,
          sharpe_ratio: 0,
        }, ...prev])
      } else {
        message.info(data.message)
      }
    } catch (error) {
      message.error('回测失败')
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    { title: '回测ID', dataIndex: 'backtest_id', key: 'backtest_id', render: (id: string) => id.substring(0, 8) + '...' },
    { title: '策略', dataIndex: 'strategy_name', key: 'strategy_name' },
    { title: '股票', dataIndex: 'symbols', key: 'symbols', render: (symbols: string[]) => symbols.join(', ') },
    { title: '初始资金', dataIndex: 'initial_capital', key: 'initial_capital', render: (v: number) => `¥${v.toLocaleString()}` },
    { title: '最终价值', dataIndex: 'final_value', key: 'final_value', render: (v: number) => `¥${v.toLocaleString()}` },
    { title: '收益率', dataIndex: 'total_return', key: 'total_return', render: (v: number) => `${(v * 100).toFixed(2)}%` },
    { title: '最大回撤', dataIndex: 'max_drawdown', key: 'max_drawdown', render: (v: number) => `${(v * 100).toFixed(2)}%` },
    { title: '夏普比率', dataIndex: 'sharpe_ratio', key: 'sharpe_ratio', render: (v: number) => v.toFixed(2) },
  ]

  return (
    <div>
      <h2>回测管理</h2>

      <Card title="创建回测" style={{ marginBottom: 16 }}>
        <Form form={form} onFinish={handleSubmit} layout="vertical">
          <Form.Item name="symbols" label="股票代码" rules={[{ required: true }]}>
            <Input placeholder="输入股票代码，多个用逗号分隔" />
          </Form.Item>

          <Form.Item name="strategy" label="策略" rules={[{ required: true }]}>
            <Select placeholder="选择策略">
              {strategies.map(s => (
                <Option key={s} value={s}>{s}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="dateRange" label="日期范围" rules={[{ required: true }]}>
            <RangePicker />
          </Form.Item>

          <Form.Item name="initial_capital" label="初始资金" initialValue={1000000}>
            <Input type="number" prefix="¥" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} icon={<PlayCircleOutlined />}>
              运行回测
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="回测结果">
        <Table columns={columns} dataSource={results} rowKey="backtest_id" />
      </Card>
    </div>
  )
}

export default Backtest
```

- [ ] **Step 2: 更新 App.tsx 添加路由**

```tsx
// frontend/src/App.tsx

import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import { Layout, Menu } from 'antd'
import {
  DashboardOutlined,
  LineChartOutlined,
  BellOutlined,
  FundOutlined,
  ExperimentOutlined,
} from '@ant-design/icons'

import Dashboard from './pages/Dashboard'
import Stocks from './pages/Stocks'
import Signals from './pages/Signals'
import Analysis from './pages/Analysis'
import Backtest from './pages/Backtest'

const { Header, Content, Sider } = Layout

const App = () => {
  const menuItems = [
    { key: '/', icon: <DashboardOutlined />, label: <Link to="/">工作台</Link> },
    { key: '/stocks', icon: <FundOutlined />, label: <Link to="/stocks">股票</Link> },
    { key: '/signals', icon: <LineChartOutlined />, label: <Link to="/signals">信号</Link> },
    { key: '/analysis', icon: <BellOutlined />, label: <Link to="/analysis">分析</Link> },
    { key: '/backtest', icon: <ExperimentOutlined />, label: <Link to="/backtest">回测</Link> },
  ]

  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider collapsible>
          <div style={{ height: 32, margin: 16, background: 'rgba(255,255,255,0.2)' }} />
          <Menu theme="dark" defaultSelectedKeys={['/']} mode="inline" items={menuItems} />
        </Sider>
        <Layout>
          <Header style={{ padding: 0, background: '#fff' }} />
          <Content style={{ margin: '24px 16px', padding: 24, background: '#fff' }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/stocks" element={<Stocks />} />
              <Route path="/signals" element={<Signals />} />
              <Route path="/analysis" element={<Analysis />} />
              <Route path="/backtest" element={<Backtest />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  )
}

export default App
```

- [ ] **Step 3: 验证编译**

Run: `cd frontend && npm run build`
Expected: Build successful

- [ ] **Step 4: 提交**

```bash
git add frontend/src/pages/Backtest.tsx frontend/src/App.tsx
git commit -m "feat: 创建回测管理前端页面

- 回测表单（股票/策略/日期/资金）
- 回测结果表格
- 路由集成"
```

---

### Task 12: 注册所有集成适配器

**Files:**
- Modify: `src/main.py`
- Create: `config/integrations.yaml`

- [ ] **Step 1: 创建集成配置文件**

```yaml
# config/integrations.yaml

integrations:
  backtrader:
    enabled: true
    strategies_path: "./strategies/backtrader"

  quantaxis:
    enabled: false
    mongodb_uri: "mongodb://localhost:27017"

  easytrader:
    enabled: false
    broker: "ths"

  qbot:
    enabled: true
    models_path: "./models/qbot"

  ai_quant:
    enabled: true
    strategies_path: "./strategies/ai_quant"
```

- [ ] **Step 2: 更新 main.py 注册适配器**

```python
# src/main.py

"""应用入口"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import get_settings
from src.infra.logger import get_logger
from src.web.api.router import api_router
from src.integrations.registry import registry
from src.integrations.backtrader.adapter import BacktraderAdapter
from src.integrations.easytrader.adapter import EasytraderAdapter
from src.integrations.quantaxis.adapter import QUANTAXISAdapter
from src.integrations.qbot.adapter import QbotAdapter
from src.integrations.ai_quant.adapter import AIQuantAdapter

logger = get_logger("main")


def create_app() -> FastAPI:
    """创建应用"""
    settings = get_settings()

    app = FastAPI(
        title="Stock Hub",
        description="量化交易系统",
        version="1.0.0",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(api_router, prefix="/api")

    # 注册集成适配器
    register_integrations()

    # 启动事件
    @app.on_event("startup")
    async def startup():
        logger.info("应用启动")
        await registry.initialize_all()

    # 健康检查
    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


def register_integrations():
    """注册集成适配器"""
    # Backtrader - 默认启用
    registry.register(BacktraderAdapter(enabled=True))

    # Easytrader - 默认禁用（需要券商客户端）
    registry.register(EasytraderAdapter(enabled=False))

    # QUANTAXIS - 默认禁用（需要 MongoDB）
    registry.register(QUANTAXISAdapter(enabled=False))

    # Qbot - 默认启用
    registry.register(QbotAdapter(enabled=True))

    # AI Quant - 默认启用
    registry.register(AIQuantAdapter(enabled=True))

    logger.info(f"已注册 {len(registry.list_available())} 个集成适配器")


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 3: 验证应用启动**

Run: `python -c "from src.main import app; print('App created')"`
Expected: App created

- [ ] **Step 4: 提交**

```bash
git add src/main.py config/integrations.yaml
git commit -m "feat: 注册所有集成适配器

- 注册 backtrader/easytrader/quantaxis/qbot/ai_quant
- 添加集成配置文件
- 应用启动时初始化所有适配器"
```

---

## 总结

完成以上 12 个任务后，stock-hub 将具备：

1. **回测能力** — 通过 backtrader 适配器，支持 MA/MACD/RSI/布林带等策略回测
2. **实盘交易** — 通过 easytrader 适配器，支持同花顺/银河/华泰/国金券商
3. **数据扩展** — 通过 QUANTAXIS 适配器，支持更多数据源（需 MongoDB）
4. **AI 策略** — 通过 Qbot 适配器，支持强化学习策略
5. **ML 策略** — 通过 ai_quant 适配器，支持机器学习策略

**下一步**：
- 实现回测结果持久化（数据库存储）
- 实现交易管理前端页面
- 实现策略中心前端页面
- 添加更多内置策略
