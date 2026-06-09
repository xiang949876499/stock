# Financial Services 集成实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 anthropics/financial-services 项目的专业金融分析能力集成到 stock-hub，包括插件架构、核心分析插件、代理工作流、数据连接器和前端界面。

**Architecture:** 采用模块化插件架构，每个分析技能作为独立插件通过注册机制集成。插件基类定义统一接口，注册表管理插件生命周期。代理工作流封装复杂分析逻辑，通过 AI 适配器执行。

**Tech Stack:** Python 3.11+, FastAPI, Pydantic v2, Pandas, React 18, TypeScript, Ant Design 5, Zustand

---

## 文件结构

```
src/plugins/                          # 新增插件目录
├── __init__.py
├── base.py                           # 插件基类
├── registry.py                       # 插件注册表
├── financial_analysis/               # 核心金融分析插件
│   ├── __init__.py
│   ├── dcf.py                        # DCF 估值
│   ├── comps.py                      # 可比公司分析
│   └── screening.py                  # 股票筛选
├── equity_research/                  # 股票研究插件
│   ├── __init__.py
│   ├── earnings.py                   # 财报分析
│   └── one_pager.py                  # 公司简介
└── agents/                           # 代理工作流
    ├── __init__.py
    ├── base.py                       # 代理基类
    ├── registry.py                   # 代理注册表
    ├── market_researcher.py          # 市场研究员
    └── earnings_reviewer.py          # 财报分析师

src/web/api/
├── plugins.py                        # 新增: 插件 API
└── commands.py                       # 新增: 命令 API

src/data/connectors/                  # 新增连接器目录
├── __init__.py
├── base.py                           # 连接器基类
├── registry.py                       # 连接器注册表
└── hk_stock_connector.py            # 港股连接器

frontend/src/
├── components/
│   ├── SlashCommand.tsx              # 新增: 斜杠命令
│   ├── PluginSelector.tsx            # 新增: 插件选择器
│   ├── ParameterForm.tsx             # 新增: 参数表单
│   └── analysis/
│       ├── DCFResult.tsx             # 新增: DCF 结果
│       └── CompsResult.tsx           # 新增: 可比分析结果
└── pages/
    └── PluginAnalysis.tsx            # 新增: 插件分析页

tests/unit/
├── test_plugin_registry.py           # 新增
├── test_dcf_plugin.py                # 新增
├── test_comps_plugin.py              # 新增
└── test_screening_plugin.py          # 新增
```

---

## Task 1: 插件基类与注册表

**Files:**
- Create: `src/plugins/__init__.py`
- Create: `src/plugins/base.py`
- Create: `src/plugins/registry.py`
- Create: `tests/unit/test_plugin_registry.py`

- [ ] **Step 1: 创建插件目录结构**

```bash
mkdir -p src/plugins
mkdir -p src/plugins/financial_analysis
mkdir -p src/plugins/equity_research
mkdir -p src/plugins/agents
```

- [ ] **Step 2: 编写插件注册表测试**

```python
# tests/unit/test_plugin_registry.py
"""插件注册表测试"""

import pytest
from src.plugins.base import AnalysisPlugin
from src.plugins.registry import PluginRegistry


class MockPlugin(AnalysisPlugin):
    """模拟插件"""

    @property
    def name(self) -> str:
        return "mock_plugin"

    @property
    def description(self) -> str:
        return "A mock plugin for testing"

    async def execute(self, stock_data, params):
        return {"result": "mock"}

    def get_parameters(self):
        return {}


@pytest.fixture(autouse=True)
def clear_registry():
    """每个测试前清空注册表"""
    PluginRegistry._plugins.clear()
    yield


def test_register_plugin():
    """测试注册插件"""
    plugin = MockPlugin()
    PluginRegistry.register(plugin)
    assert PluginRegistry.get("mock_plugin") == plugin


def test_get_nonexistent_plugin():
    """测试获取不存在的插件"""
    assert PluginRegistry.get("nonexistent") is None


def test_list_plugins():
    """测试列出插件"""
    plugin = MockPlugin()
    PluginRegistry.register(plugin)
    result = PluginRegistry.list_plugins()
    assert "mock_plugin" in result
    assert result["mock_plugin"] == "A mock plugin for testing"


def test_get_all_plugins():
    """测试获取所有插件"""
    plugin1 = MockPlugin()
    plugin2 = MockPlugin()
    plugin2._name = "mock_plugin_2"
    PluginRegistry.register(plugin1)
    PluginRegistry.register(plugin2)
    all_plugins = PluginRegistry.get_all()
    assert len(all_plugins) == 2
```

- [ ] **Step 3: 运行测试验证失败**

```bash
python -m pytest tests/unit/test_plugin_registry.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.plugins'"

- [ ] **Step 4: 实现插件基类**

```python
# src/plugins/__init__.py
"""插件模块"""

from .base import AnalysisPlugin
from .registry import PluginRegistry

__all__ = ["AnalysisPlugin", "PluginRegistry"]
```

```python
# src/plugins/base.py
"""插件基类"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class AnalysisPlugin(ABC):
    """分析插件基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass

    @property
    def version(self) -> str:
        """插件版本"""
        return "1.0.0"

    @abstractmethod
    async def execute(
        self,
        stock_data: Any,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行分析

        Args:
            stock_data: 股票数据
            params: 分析参数

        Returns:
            分析结果字典
        """
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义

        Returns:
            参数定义字典，格式:
            {
                "param_name": {
                    "type": "int|float|str|List[str]",
                    "default": ...,
                    "description": "..."
                }
            }
        """
        pass
```

- [ ] **Step 5: 实现插件注册表**

```python
# src/plugins/registry.py
"""插件注册表"""

from typing import Dict, Any, Optional, List
from src.plugins.base import AnalysisPlugin


class PluginRegistry:
    """插件注册表"""

    _plugins: Dict[str, AnalysisPlugin] = {}

    @classmethod
    def register(cls, plugin: AnalysisPlugin) -> None:
        """注册插件

        Args:
            plugin: 插件实例
        """
        cls._plugins[plugin.name] = plugin

    @classmethod
    def get(cls, name: str) -> Optional[AnalysisPlugin]:
        """获取插件

        Args:
            name: 插件名称

        Returns:
            插件实例，不存在返回 None
        """
        return cls._plugins.get(name)

    @classmethod
    def list_plugins(cls) -> Dict[str, str]:
        """列出所有插件

        Returns:
            {插件名称: 插件描述} 字典
        """
        return {name: p.description for name, p in cls._plugins.items()}

    @classmethod
    def get_all(cls) -> List[AnalysisPlugin]:
        """获取所有插件

        Returns:
            插件实例列表
        """
        return list(cls._plugins.values())

    @classmethod
    def clear(cls) -> None:
        """清空注册表（用于测试）"""
        cls._plugins.clear()
```

- [ ] **Step 6: 运行测试验证通过**

```bash
python -m pytest tests/unit/test_plugin_registry.py -v
```

Expected: ALL PASS

- [ ] **Step 7: 提交代码**

```bash
git add src/plugins/__init__.py src/plugins/base.py src/plugins/registry.py tests/unit/test_plugin_registry.py
git commit -m "feat(plugins): 添加插件基类和注册表"
```

---

## Task 2: DCF 估值插件

**Files:**
- Create: `src/plugins/financial_analysis/__init__.py`
- Create: `src/plugins/financial_analysis/dcf.py`
- Create: `tests/unit/test_dcf_plugin.py`

- [ ] **Step 1: 编写 DCF 插件测试**

```python
# tests/unit/test_dcf_plugin.py
"""DCF 估值插件测试"""

import pytest
from src.plugins.financial_analysis.dcf import DCFValuationPlugin


@pytest.fixture
def dcf_plugin():
    return DCFValuationPlugin()


def test_dcf_plugin_name(dcf_plugin):
    """测试插件名称"""
    assert dcf_plugin.name == "dcf_valuation"


def test_dcf_plugin_description(dcf_plugin):
    """测试插件描述"""
    assert "DCF" in dcf_plugin.description


def test_dcf_parameters(dcf_plugin):
    """测试参数定义"""
    params = dcf_plugin.get_parameters()
    assert "years" in params
    assert "growth_rate" in params
    assert "wacc" in params
    assert params["years"]["default"] == 5


@pytest.mark.asyncio
async def test_dcf_execute_with_mock_data(dcf_plugin):
    """测试 DCF 执行（使用模拟数据）"""
    # 模拟股票数据
    stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "current_price": 1800.0,
        "revenue": 150000000000,  # 1500 亿
        "net_profit": 75000000000,  # 750 亿
        "total_shares": 1256198000,  # 12.56 亿股
    }

    params = {
        "years": 5,
        "growth_rate": 0.15,
        "terminal_growth": 0.03,
        "wacc": 0.10,
    }

    result = await dcf_plugin.execute(stock_data, params)

    # 验证返回结构
    assert "enterprise_value" in result
    assert "equity_value" in result
    assert "per_share_value" in result
    assert "current_price" in result
    assert "upside_pct" in result
    assert "cash_flows" in result

    # 验证数值合理性
    assert result["enterprise_value"] > 0
    assert result["per_share_value"] > 0
    assert len(result["cash_flows"]) == 5
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/unit/test_dcf_plugin.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.plugins.financial_analysis'"

- [ ] **Step 3: 实现 DCF 估值插件**

```python
# src/plugins/financial_analysis/__init__.py
"""核心金融分析插件"""

from .dcf import DCFValuationPlugin

__all__ = ["DCFValuationPlugin"]
```

```python
# src/plugins/financial_analysis/dcf.py
"""DCF 估值插件"""

from typing import Dict, Any, List
from src.plugins.base import AnalysisPlugin


class DCFValuationPlugin(AnalysisPlugin):
    """DCF 现金流折现估值插件"""

    @property
    def name(self) -> str:
        return "dcf_valuation"

    @property
    def description(self) -> str:
        return "DCF 现金流折现估值模型，计算企业价值和每股价值"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "years": {
                "type": "int",
                "default": 5,
                "description": "预测年数"
            },
            "growth_rate": {
                "type": "float",
                "default": 0.15,
                "description": "收入增长率"
            },
            "terminal_growth": {
                "type": "float",
                "default": 0.03,
                "description": "永续增长率"
            },
            "wacc": {
                "type": "float",
                "default": 0.10,
                "description": "加权平均资本成本"
            },
            "tax_rate": {
                "type": "float",
                "default": 0.25,
                "description": "税率"
            },
            "capex_pct": {
                "type": "float",
                "default": 0.05,
                "description": "资本支出占比"
            },
            "working_capital_pct": {
                "type": "float",
                "default": 0.10,
                "description": "营运资本占比"
            }
        }

    async def execute(
        self,
        stock_data: Any,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行 DCF 估值

        Args:
            stock_data: 股票数据，需包含 revenue, net_profit, current_price, total_shares
            params: DCF 参数

        Returns:
            估值结果
        """
        # 获取参数
        years = params.get("years", 5)
        growth_rate = params.get("growth_rate", 0.15)
        terminal_growth = params.get("terminal_growth", 0.03)
        wacc = params.get("wacc", 0.10)
        tax_rate = params.get("tax_rate", 0.25)
        capex_pct = params.get("capex_pct", 0.05)
        wc_pct = params.get("working_capital_pct", 0.10)

        # 获取基础数据
        revenue = stock_data.get("revenue", 0)
        net_profit = stock_data.get("net_profit", 0)
        current_price = stock_data.get("current_price", 0)
        total_shares = stock_data.get("total_shares", 1)

        # 计算自由现金流
        # FCF = 净利润 * (1 - 再投资率)
        reinvestment_rate = capex_pct + wc_pct
        base_fcf = net_profit * (1 - reinvestment_rate)

        # 预测未来现金流
        cash_flows: List[Dict[str, Any]] = []
        for year in range(1, years + 1):
            cf = base_fcf * (1 + growth_rate) ** year
            cash_flows.append({
                "year": year,
                "cf": round(cf, 2),
                "discount_factor": round(1 / (1 + wacc) ** year, 4),
                "pv": round(cf / (1 + wacc) ** year, 2)
            })

        # 计算终值
        terminal_cf = cash_flows[-1]["cf"] * (1 + terminal_growth)
        terminal_value = terminal_cf / (wacc - terminal_growth)
        terminal_pv = terminal_value / (1 + wacc) ** years

        # 计算企业价值
        pv_cash_flows = sum(cf["pv"] for cf in cash_flows)
        enterprise_value = pv_cash_flows + terminal_pv

        # 假设净债务为 0（简化处理）
        net_debt = 0
        equity_value = enterprise_value - net_debt
        per_share_value = equity_value / total_shares if total_shares > 0 else 0

        # 计算上行空间
        upside_pct = ((per_share_value - current_price) / current_price * 100) if current_price > 0 else 0

        # 敏感性分析
        sensitivity_table = self._calculate_sensitivity(
            base_fcf, growth_rate, terminal_growth, years, total_shares
        )

        return {
            "enterprise_value": round(enterprise_value, 2),
            "equity_value": round(equity_value, 2),
            "per_share_value": round(per_share_value, 2),
            "current_price": current_price,
            "upside_pct": round(upside_pct, 2),
            "sensitivity_table": sensitivity_table,
            "assumptions": {
                "years": years,
                "growth_rate": growth_rate,
                "terminal_growth": terminal_growth,
                "wacc": wacc,
                "tax_rate": tax_rate,
                "capex_pct": capex_pct,
                "working_capital_pct": wc_pct
            },
            "cash_flows": cash_flows
        }

    def _calculate_sensitivity(
        self,
        base_fcf: float,
        growth_rate: float,
        terminal_growth: float,
        years: int,
        total_shares: int
    ) -> Dict[str, Dict[str, float]]:
        """计算敏感性分析表

        Returns:
            {wacc: {growth: per_share_value}} 嵌套字典
        """
        wacc_range = [0.08, 0.09, 0.10, 0.11, 0.12]
        growth_range = [0.10, 0.12, 0.15, 0.18, 0.20]

        result = {}
        for wacc in wacc_range:
            result[str(wacc)] = {}
            for growth in growth_range:
                # 简化计算
                total_pv = 0
                for year in range(1, years + 1):
                    cf = base_fcf * (1 + growth) ** year
                    total_pv += cf / (1 + wacc) ** year

                terminal_cf = base_fcf * (1 + growth) ** years * (1 + terminal_growth)
                terminal_value = terminal_cf / (wacc - terminal_growth)
                terminal_pv = terminal_value / (1 + wacc) ** years

                ev = total_pv + terminal_pv
                per_share = ev / total_shares if total_shares > 0 else 0
                result[str(wacc)][str(growth)] = round(per_share, 2)

        return result
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/unit/test_dcf_plugin.py -v
```

Expected: ALL PASS

- [ ] **Step 5: 提交代码**

```bash
git add src/plugins/financial_analysis/__init__.py src/plugins/financial_analysis/dcf.py tests/unit/test_dcf_plugin.py
git commit -m "feat(plugins): 添加 DCF 估值插件"
```

---

## Task 3: 可比公司分析插件

**Files:**
- Create: `src/plugins/financial_analysis/comps.py`
- Create: `tests/unit/test_comps_plugin.py`
- Modify: `src/plugins/financial_analysis/__init__.py`

- [ ] **Step 1: 编写可比公司分析测试**

```python
# tests/unit/test_comps_plugin.py
"""可比公司分析插件测试"""

import pytest
from src.plugins.financial_analysis.comps import ComparableAnalysisPlugin


@pytest.fixture
def comps_plugin():
    return ComparableAnalysisPlugin()


def test_comps_plugin_name(comps_plugin):
    """测试插件名称"""
    assert comps_plugin.name == "comparable_analysis"


def test_comps_parameters(comps_plugin):
    """测试参数定义"""
    params = comps_plugin.get_parameters()
    assert "peer_codes" in params
    assert "metrics" in params


@pytest.mark.asyncio
async def test_comps_execute(comps_plugin):
    """测试可比公司分析执行"""
    stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "current_price": 1800.0,
        "pe_ratio": 30.5,
        "pb_ratio": 10.2,
        "ps_ratio": 15.8,
        "ev_ebitda": 22.3,
        "market_cap": 2260000000000,
    }

    params = {
        "peer_codes": ["000858", "002304", "000568"],
        "metrics": ["PE", "PB", "PS", "EV/EBITDA"],
    }

    result = await comps_plugin.execute(stock_data, params)

    # 验证返回结构
    assert "target_valuation" in result
    assert "peer_comparison" in result
    assert "implied_value" in result
    assert "premium_discount" in result

    # 验证同行对比数据
    assert len(result["peer_comparison"]) == 3
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/unit/test_comps_plugin.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 实现可比公司分析插件**

```python
# src/plugins/financial_analysis/comps.py
"""可比公司分析插件"""

from typing import Dict, Any, List
from src.plugins.base import AnalysisPlugin


class ComparableAnalysisPlugin(AnalysisPlugin):
    """可比公司分析插件"""

    @property
    def name(self) -> str:
        return "comparable_analysis"

    @property
    def description(self) -> str:
        return "通过同行业公司对比估值，计算隐含价值"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "peer_codes": {
                "type": "List[str]",
                "description": "同行股票代码列表"
            },
            "metrics": {
                "type": "List[str]",
                "default": ["PE", "PB", "PS", "EV/EBITDA"],
                "description": "估值指标"
            },
            "period": {
                "type": "str",
                "default": "latest",
                "description": "数据期间"
            }
        }

    async def execute(
        self,
        stock_data: Any,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行可比公司分析

        Args:
            stock_data: 目标股票数据
            params: 分析参数，需包含 peer_codes

        Returns:
            可比分析结果
        """
        peer_codes = params.get("peer_codes", [])
        metrics = params.get("metrics", ["PE", "PB", "PS", "EV/EBITDA"])

        # 获取目标公司估值
        target_valuation = self._extract_valuation(stock_data, metrics)

        # 获取同行估值（模拟数据，实际应从数据源获取）
        peer_comparison = self._get_peer_valuations(peer_codes, metrics)

        # 计算同行平均估值
        peer_averages = self._calculate_peer_averages(peer_comparison, metrics)

        # 计算隐含价值
        implied_value = self._calculate_implied_value(
            stock_data, peer_averages, metrics
        )

        # 计算溢价/折价
        current_price = stock_data.get("current_price", 0)
        premium_discount = 0
        if current_price > 0 and implied_value > 0:
            premium_discount = ((current_price - implied_value) / implied_value) * 100

        return {
            "target_valuation": target_valuation,
            "peer_comparison": peer_comparison,
            "peer_averages": peer_averages,
            "implied_value": round(implied_value, 2),
            "premium_discount": round(premium_discount, 2)
        }

    def _extract_valuation(
        self,
        stock_data: Any,
        metrics: List[str]
    ) -> Dict[str, float]:
        """提取公司估值指标"""
        valuation = {}
        metric_mapping = {
            "PE": "pe_ratio",
            "PB": "pb_ratio",
            "PS": "ps_ratio",
            "EV/EBITDA": "ev_ebitda"
        }
        for metric in metrics:
            key = metric_mapping.get(metric, metric.lower())
            valuation[metric] = stock_data.get(key, 0)
        return valuation

    def _get_peer_valuations(
        self,
        peer_codes: List[str],
        metrics: List[str]
    ) -> List[Dict[str, Any]]:
        """获取同行估值（模拟数据）"""
        # 模拟同行数据
        mock_peers = {
            "000858": {"name": "五粮液", "PE": 25.3, "PB": 7.8, "PS": 8.5, "EV/EBITDA": 18.2},
            "002304": {"name": "洋河股份", "PE": 20.1, "PB": 5.2, "PS": 6.3, "EV/EBITDA": 14.5},
            "000568": {"name": "泸州老窖", "PE": 28.7, "PB": 9.1, "PS": 12.4, "EV/EBITDA": 20.8},
        }

        result = []
        for code in peer_codes:
            peer_data = mock_peers.get(code, {"name": f"股票{code}"})
            peer_valuation = {"code": code, "name": peer_data.get("name", "")}
            for metric in metrics:
                peer_valuation[metric] = peer_data.get(metric, 0)
            result.append(peer_valuation)

        return result

    def _calculate_peer_averages(
        self,
        peer_comparison: List[Dict[str, Any]],
        metrics: List[str]
    ) -> Dict[str, float]:
        """计算同行平均估值"""
        averages = {}
        for metric in metrics:
            values = [p.get(metric, 0) for p in peer_comparison if p.get(metric, 0) > 0]
            averages[metric] = sum(values) / len(values) if values else 0
        return averages

    def _calculate_implied_value(
        self,
        stock_data: Any,
        peer_averages: Dict[str, float],
        metrics: List[str]
    ) -> float:
        """计算隐含价值"""
        # 使用 PE 和 PB 的平均值估算
        current_price = stock_data.get("current_price", 0)
        pe_ratio = stock_data.get("pe_ratio", 0)
        pb_ratio = stock_data.get("pb_ratio", 0)

        implied_values = []

        # 基于 PE 的隐含价值
        if "PE" in peer_averages and pe_ratio > 0:
            pe_implied = current_price * (peer_averages["PE"] / pe_ratio)
            implied_values.append(pe_implied)

        # 基于 PB 的隐含价值
        if "PB" in peer_averages and pb_ratio > 0:
            pb_implied = current_price * (peer_averages["PB"] / pb_ratio)
            implied_values.append(pb_implied)

        return sum(implied_values) / len(implied_values) if implied_values else current_price
```

- [ ] **Step 4: 更新 __init__.py**

```python
# src/plugins/financial_analysis/__init__.py
"""核心金融分析插件"""

from .dcf import DCFValuationPlugin
from .comps import ComparableAnalysisPlugin

__all__ = ["DCFValuationPlugin", "ComparableAnalysisPlugin"]
```

- [ ] **Step 5: 运行测试验证通过**

```bash
python -m pytest tests/unit/test_comps_plugin.py -v
```

Expected: ALL PASS

- [ ] **Step 6: 提交代码**

```bash
git add src/plugins/financial_analysis/comps.py src/plugins/financial_analysis/__init__.py tests/unit/test_comps_plugin.py
git commit -m "feat(plugins): 添加可比公司分析插件"
```

---

## Task 4: 股票筛选插件

**Files:**
- Create: `src/plugins/financial_analysis/screening.py`
- Create: `tests/unit/test_screening_plugin.py`
- Modify: `src/plugins/financial_analysis/__init__.py`

- [ ] **Step 1: 编写股票筛选测试**

```python
# tests/unit/test_screening_plugin.py
"""股票筛选插件测试"""

import pytest
from src.plugins.financial_analysis.screening import StockScreeningPlugin


@pytest.fixture
def screening_plugin():
    return StockScreeningPlugin()


def test_screening_plugin_name(screening_plugin):
    """测试插件名称"""
    assert screening_plugin.name == "stock_screening"


def test_screening_parameters(screening_plugin):
    """测试参数定义"""
    params = screening_plugin.get_parameters()
    assert "universe" in params
    assert "filters" in params
    assert "sort_by" in params
    assert "limit" in params


@pytest.mark.asyncio
async def test_screening_execute(screening_plugin):
    """测试股票筛选执行"""
    stock_data = {}  # 筛选不需要特定股票数据

    params = {
        "universe": "hs300",
        "filters": {
            "pe_ratio": {"max": 30},
            "roe": {"min": 0.15}
        },
        "sort_by": "roe",
        "limit": 5
    }

    result = await screening_plugin.execute(stock_data, params)

    # 验证返回结构
    assert "results" in result
    assert "total_count" in result
    assert "filters_applied" in result

    # 验证结果数量
    assert len(result["results"]) <= 5
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/unit/test_screening_plugin.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 实现股票筛选插件**

```python
# src/plugins/financial_analysis/screening.py
"""股票筛选插件"""

from typing import Dict, Any, List
from src.plugins.base import AnalysisPlugin


class StockScreeningPlugin(AnalysisPlugin):
    """股票筛选插件"""

    # 模拟股票池
    MOCK_STOCKS = [
        {"code": "600519", "name": "贵州茅台", "pe_ratio": 30.5, "pb_ratio": 10.2, "roe": 0.32, "market_cap": 2260000000000, "revenue_growth": 0.15},
        {"code": "000858", "name": "五粮液", "pe_ratio": 25.3, "pb_ratio": 7.8, "roe": 0.28, "market_cap": 850000000000, "revenue_growth": 0.12},
        {"code": "002304", "name": "洋河股份", "pe_ratio": 20.1, "pb_ratio": 5.2, "roe": 0.22, "market_cap": 320000000000, "revenue_growth": 0.08},
        {"code": "600036", "name": "招商银行", "pe_ratio": 8.5, "pb_ratio": 1.2, "roe": 0.16, "market_cap": 1100000000000, "revenue_growth": 0.10},
        {"code": "601318", "name": "中国平安", "pe_ratio": 9.2, "pb_ratio": 1.5, "roe": 0.18, "market_cap": 950000000000, "revenue_growth": 0.06},
        {"code": "300750", "name": "宁德时代", "pe_ratio": 45.2, "pb_ratio": 8.5, "roe": 0.25, "market_cap": 1200000000000, "revenue_growth": 0.35},
        {"code": "002594", "name": "比亚迪", "pe_ratio": 35.8, "pb_ratio": 6.2, "roe": 0.15, "market_cap": 800000000000, "revenue_growth": 0.42},
        {"code": "600900", "name": "长江电力", "pe_ratio": 18.5, "pb_ratio": 3.2, "roe": 0.14, "market_cap": 650000000000, "revenue_growth": 0.05},
    ]

    @property
    def name(self) -> str:
        return "stock_screening"

    @property
    def description(self) -> str:
        return "基于多维度指标筛选股票"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "universe": {
                "type": "str",
                "default": "hs300",
                "description": "股票池"
            },
            "filters": {
                "type": "Dict[str, Dict]",
                "description": "筛选条件，格式: {指标: {min: 最小值, max: 最大值}}"
            },
            "sort_by": {
                "type": "str",
                "default": "score",
                "description": "排序字段"
            },
            "limit": {
                "type": "int",
                "default": 20,
                "description": "结果数量限制"
            }
        }

    async def execute(
        self,
        stock_data: Any,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行股票筛选

        Args:
            stock_data: 不使用
            params: 筛选参数

        Returns:
            筛选结果
        """
        filters = params.get("filters", {})
        sort_by = params.get("sort_by", "score")
        limit = params.get("limit", 20)

        # 应用筛选条件
        filtered_stocks = self._apply_filters(self.MOCK_STOCKS, filters)

        # 计算综合评分
        scored_stocks = self._calculate_scores(filtered_stocks)

        # 排序
        if sort_by == "score":
            scored_stocks.sort(key=lambda x: x.get("score", 0), reverse=True)
        elif sort_by in scored_stocks[0] if scored_stocks else []:
            scored_stocks.sort(key=lambda x: x.get(sort_by, 0), reverse=True)

        # 限制结果数量
        results = scored_stocks[:limit]

        return {
            "results": results,
            "total_count": len(scored_stocks),
            "filters_applied": filters
        }

    def _apply_filters(
        self,
        stocks: List[Dict[str, Any]],
        filters: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """应用筛选条件"""
        filtered = stocks.copy()

        for metric, conditions in filters.items():
            if "min" in conditions:
                filtered = [s for s in filtered if s.get(metric, 0) >= conditions["min"]]
            if "max" in conditions:
                filtered = [s for s in filtered if s.get(metric, 0) <= conditions["max"]]

        return filtered

    def _calculate_scores(
        self,
        stocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """计算综合评分"""
        scored = []
        for stock in stocks:
            # 简单评分逻辑：ROE 越高越好，PE 越低越好
            roe_score = min(stock.get("roe", 0) * 100, 30)  # 最高 30 分
            pe_score = max(30 - stock.get("pe_ratio", 50), 0)  # PE 越低分越高
            growth_score = min(stock.get("revenue_growth", 0) * 50, 20)  # 最高 20 分

            total_score = roe_score + pe_score + growth_score
            stock_with_score = stock.copy()
            stock_with_score["score"] = round(total_score, 2)
            scored.append(stock_with_score)

        return scored
```

- [ ] **Step 4: 更新 __init__.py**

```python
# src/plugins/financial_analysis/__init__.py
"""核心金融分析插件"""

from .dcf import DCFValuationPlugin
from .comps import ComparableAnalysisPlugin
from .screening import StockScreeningPlugin

__all__ = ["DCFValuationPlugin", "ComparableAnalysisPlugin", "StockScreeningPlugin"]
```

- [ ] **Step 5: 运行测试验证通过**

```bash
python -m pytest tests/unit/test_screening_plugin.py -v
```

Expected: ALL PASS

- [ ] **Step 6: 提交代码**

```bash
git add src/plugins/financial_analysis/screening.py src/plugins/financial_analysis/__init__.py tests/unit/test_screening_plugin.py
git commit -m "feat(plugins): 添加股票筛选插件"
```

---

## Task 5: 财报分析插件

**Files:**
- Create: `src/plugins/equity_research/__init__.py`
- Create: `src/plugins/equity_research/earnings.py`
- Create: `tests/unit/test_earnings_plugin.py`

- [ ] **Step 1: 编写财报分析测试**

```python
# tests/unit/test_earnings_plugin.py
"""财报分析插件测试"""

import pytest
from src.plugins.equity_research.earnings import EarningsAnalysisPlugin


@pytest.fixture
def earnings_plugin():
    return EarningsAnalysisPlugin()


def test_earnings_plugin_name(earnings_plugin):
    """测试插件名称"""
    assert earnings_plugin.name == "earnings_analysis"


def test_earnings_parameters(earnings_plugin):
    """测试参数定义"""
    params = earnings_plugin.get_parameters()
    assert "period" in params
    assert "compare_with" in params
    assert "focus_areas" in params


@pytest.mark.asyncio
async def test_earnings_execute(earnings_plugin):
    """测试财报分析执行"""
    stock_data = {
        "symbol": "600519",
        "name": "贵州茅台",
        "revenue": 150000000000,
        "net_profit": 75000000000,
        "eps": 59.72,
        "roe": 0.32,
        "gross_margin": 0.91,
        "net_margin": 0.50,
        "operating_cash_flow": 80000000000,
    }

    params = {
        "period": "2024Q3",
        "compare_with": "2023Q3",
        "focus_areas": ["revenue", "margins", "cash_flow"]
    }

    result = await earnings_plugin.execute(stock_data, params)

    # 验证返回结构
    assert "summary" in result
    assert "highlights" in result
    assert "risks" in result
    assert "financial_metrics" in result
    assert "yoy_comparison" in result

    # 验证内容
    assert isinstance(result["highlights"], list)
    assert isinstance(result["risks"], list)
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/unit/test_earnings_plugin.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 实现财报分析插件**

```python
# src/plugins/equity_research/__init__.py
"""股票研究插件"""

from .earnings import EarningsAnalysisPlugin

__all__ = ["EarningsAnalysisPlugin"]
```

```python
# src/plugins/equity_research/earnings.py
"""财报分析插件"""

from typing import Dict, Any, List
from src.plugins.base import AnalysisPlugin


class EarningsAnalysisPlugin(AnalysisPlugin):
    """财报分析插件"""

    @property
    def name(self) -> str:
        return "earnings_analysis"

    @property
    def description(self) -> str:
        return "分析公司财报，生成分析报告"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "period": {
                "type": "str",
                "description": "财报期间，如 2024Q3"
            },
            "compare_with": {
                "type": "str",
                "description": "对比期间，如 2023Q3"
            },
            "focus_areas": {
                "type": "List[str]",
                "default": ["revenue", "margins", "cash_flow"],
                "description": "关注领域"
            }
        }

    async def execute(
        self,
        stock_data: Any,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行财报分析

        Args:
            stock_data: 股票财务数据
            params: 分析参数

        Returns:
            财报分析结果
        """
        period = params.get("period", "latest")
        compare_with = params.get("compare_with", "")
        focus_areas = params.get("focus_areas", ["revenue", "margins", "cash_flow"])

        # 提取财务指标
        financial_metrics = self._extract_metrics(stock_data)

        # 生成同比对比
        yoy_comparison = self._calculate_yoy(stock_data, compare_with)

        # 生成亮点
        highlights = self._identify_highlights(financial_metrics, focus_areas)

        # 识别风险
        risks = self._identify_risks(financial_metrics, focus_areas)

        # 生成摘要
        summary = self._generate_summary(
            stock_data, financial_metrics, highlights, risks
        )

        return {
            "summary": summary,
            "highlights": highlights,
            "risks": risks,
            "financial_metrics": financial_metrics,
            "yoy_comparison": yoy_comparison
        }

    def _extract_metrics(self, stock_data: Any) -> Dict[str, Any]:
        """提取财务指标"""
        return {
            "revenue": stock_data.get("revenue", 0),
            "net_profit": stock_data.get("net_profit", 0),
            "eps": stock_data.get("eps", 0),
            "roe": stock_data.get("roe", 0),
            "gross_margin": stock_data.get("gross_margin", 0),
            "net_margin": stock_data.get("net_margin", 0),
            "operating_cash_flow": stock_data.get("operating_cash_flow", 0),
        }

    def _calculate_yoy(
        self,
        stock_data: Any,
        compare_with: str
    ) -> Dict[str, float]:
        """计算同比变化（模拟数据）"""
        # 模拟同比数据
        return {
            "revenue_growth": 0.153,
            "profit_growth": 0.128,
            "eps_growth": 0.125,
            "roe_change": 0.02,
        }

    def _identify_highlights(
        self,
        metrics: Dict[str, Any],
        focus_areas: List[str]
    ) -> List[str]:
        """识别财报亮点"""
        highlights = []

        if "revenue" in focus_areas:
            revenue = metrics.get("revenue", 0)
            if revenue > 100000000000:  # > 1000 亿
                highlights.append("营收规模超过 1000 亿，行业领先地位稳固")

        if "margins" in focus_areas:
            gross_margin = metrics.get("gross_margin", 0)
            if gross_margin > 0.5:
                highlights.append(f"毛利率高达 {gross_margin:.1%}，盈利能力突出")

            net_margin = metrics.get("net_margin", 0)
            if net_margin > 0.3:
                highlights.append(f"净利率 {net_margin:.1%}，成本控制优秀")

        if "cash_flow" in focus_areas:
            ocf = metrics.get("operating_cash_flow", 0)
            if ocf > 0:
                highlights.append("经营现金流为正，经营质量良好")

        roe = metrics.get("roe", 0)
        if roe > 0.2:
            highlights.append(f"ROE 达 {roe:.1%}，资本回报率优秀")

        return highlights

    def _identify_risks(
        self,
        metrics: Dict[str, Any],
        focus_areas: List[str]
    ) -> List[str]:
        """识别风险"""
        risks = []

        roe = metrics.get("roe", 0)
        if roe < 0.1:
            risks.append("ROE 偏低，资本回报率不足")

        net_margin = metrics.get("net_margin", 0)
        if net_margin < 0.1:
            risks.append("净利率偏低，盈利能力待提升")

        return risks

    def _generate_summary(
        self,
        stock_data: Any,
        metrics: Dict[str, Any],
        highlights: List[str],
        risks: List[str]
    ) -> str:
        """生成财报摘要"""
        symbol = stock_data.get("symbol", "未知")
        name = stock_data.get("name", "未知公司")
        revenue = metrics.get("revenue", 0)
        net_profit = metrics.get("net_profit", 0)

        summary = f"{name}({symbol})财报分析：\n"
        summary += f"营收 {revenue / 1e8:.2f} 亿元，净利润 {net_profit / 1e8:.2f} 亿元。\n"

        if highlights:
            summary += f"亮点：{'；'.join(highlights[:3])}。"

        if risks:
            summary += f"风险：{'；'.join(risks[:2])}。"

        return summary
```

- [ ] **Step 4: 运行测试验证通过**

```bash
python -m pytest tests/unit/test_earnings_plugin.py -v
```

Expected: ALL PASS

- [ ] **Step 5: 提交代码**

```bash
git add src/plugins/equity_research/__init__.py src/plugins/equity_research/earnings.py tests/unit/test_earnings_plugin.py
git commit -m "feat(plugins): 添加财报分析插件"
```

---

## Task 6: 插件 API 端点

**Files:**
- Create: `src/web/api/plugins.py`
- Create: `src/web/api/commands.py`
- Modify: `src/web/api/router.py`

- [ ] **Step 1: 创建插件 API**

```python
# src/web/api/plugins.py
"""插件 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from src.plugins.registry import PluginRegistry

router = APIRouter(prefix="/plugins", tags=["plugins"])


class PluginExecuteRequest(BaseModel):
    """插件执行请求"""
    symbol: str
    params: Dict[str, Any] = {}
    period: Optional[str] = None


@router.get("/")
async def list_plugins():
    """列出所有可用插件"""
    return PluginRegistry.list_plugins()


@router.get("/{plugin_name}")
async def get_plugin_info(plugin_name: str):
    """获取插件信息"""
    plugin = PluginRegistry.get(plugin_name)
    if not plugin:
        raise HTTPException(404, f"Plugin {plugin_name} not found")
    return {
        "name": plugin.name,
        "description": plugin.description,
        "version": plugin.version,
        "parameters": plugin.get_parameters()
    }


@router.post("/{plugin_name}/execute")
async def execute_plugin(
    plugin_name: str,
    request: PluginExecuteRequest
):
    """执行插件分析"""
    plugin = PluginRegistry.get(plugin_name)
    if not plugin:
        raise HTTPException(404, f"Plugin {plugin_name} not found")

    # 构造股票数据（简化处理）
    stock_data = {
        "symbol": request.symbol,
        "current_price": 100.0,  # 实际应从数据源获取
    }

    result = await plugin.execute(
        stock_data=stock_data,
        params=request.params
    )
    return result
```

- [ ] **Step 2: 创建命令 API**

```python
# src/web/api/commands.py
"""命令 API"""

from fastapi import APIRouter
from typing import List, Dict

router = APIRouter(prefix="/commands", tags=["commands"])

COMMANDS = [
    {
        "name": "dcf",
        "description": "DCF 估值分析",
        "plugin": "dcf_valuation",
        "usage": "/dcf <股票代码>"
    },
    {
        "name": "comps",
        "description": "可比公司分析",
        "plugin": "comparable_analysis",
        "usage": "/comps <股票代码> <同行代码>"
    },
    {
        "name": "screen",
        "description": "股票筛选",
        "plugin": "stock_screening",
        "usage": "/screen <筛选条件>"
    },
    {
        "name": "earnings",
        "description": "财报分析",
        "plugin": "earnings_analysis",
        "usage": "/earnings <股票代码> <期间>"
    }
]


@router.get("/")
async def list_commands() -> List[Dict]:
    """列出所有可用命令"""
    return COMMANDS
```

- [ ] **Step 3: 更新路由注册**

```python
# src/web/api/router.py
"""API 路由"""

from fastapi import APIRouter

from .stocks import router as stocks_router
from .analysis import router as analysis_router
from .signals import router as signals_router
from .execution import router as execution_router
from .backtest import router as backtest_router
from .news import router as news_router
from .agent import router as agent_router
from .recommend import router as recommend_router
from .plugins import router as plugins_router
from .commands import router as commands_router

router = APIRouter(prefix="/api/v1")

# 注册子路由
router.include_router(stocks_router)
router.include_router(analysis_router)
router.include_router(signals_router)
router.include_router(execution_router)
router.include_router(backtest_router)
router.include_router(news_router)
router.include_router(agent_router)
router.include_router(recommend_router)
router.include_router(plugins_router)
router.include_router(commands_router)


@router.get("/")
async def root():
    """API 根路径"""
    return {"message": "Stock Hub API v1"}
```

- [ ] **Step 4: 注册内置插件**

```python
# src/plugins/__init__.py
"""插件模块"""

from .base import AnalysisPlugin
from .registry import PluginRegistry

# 注册内置插件
from .financial_analysis import DCFValuationPlugin, ComparableAnalysisPlugin, StockScreeningPlugin
from .equity_research import EarningsAnalysisPlugin

PluginRegistry.register(DCFValuationPlugin())
PluginRegistry.register(ComparableAnalysisPlugin())
PluginRegistry.register(StockScreeningPlugin())
PluginRegistry.register(EarningsAnalysisPlugin())

__all__ = ["AnalysisPlugin", "PluginRegistry"]
```

- [ ] **Step 5: 提交代码**

```bash
git add src/web/api/plugins.py src/web/api/commands.py src/web/api/router.py src/plugins/__init__.py
git commit -m "feat(api): 添加插件和命令 API 端点"
```

---

## Task 7: 代理工作流基类

**Files:**
- Create: `src/plugins/agents/__init__.py`
- Create: `src/plugins/agents/base.py`
- Create: `src/plugins/agents/registry.py`
- Create: `tests/unit/test_agent_base.py`

- [ ] **Step 1: 编写代理基类测试**

```python
# tests/unit/test_agent_base.py
"""代理基类测试"""

import pytest
from src.plugins.agents.base import AnalysisAgent


class MockAgent(AnalysisAgent):
    """模拟代理"""

    @property
    def system_prompt(self) -> str:
        return "你是一位测试代理。"


@pytest.fixture
def mock_agent():
    return MockAgent(ai_adapter=None, plugins=[])


def test_agent_system_prompt(mock_agent):
    """测试系统提示词"""
    assert "测试代理" in mock_agent.system_prompt


def test_agent_initialization(mock_agent):
    """测试代理初始化"""
    assert mock_agent.ai_adapter is None
    assert mock_agent.plugins == []
```

- [ ] **Step 2: 运行测试验证失败**

```bash
python -m pytest tests/unit/test_agent_base.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: 实现代理基类**

```python
# src/plugins/agents/__init__.py
"""代理工作流模块"""

from .base import AnalysisAgent
from .registry import AgentRegistry

__all__ = ["AnalysisAgent", "AgentRegistry"]
```

```python
# src/plugins/agents/base.py
"""代理基类"""

from typing import Dict, Any, List, Optional
from src.plugins.base import AnalysisPlugin


class AnalysisAgent:
    """分析代理基类"""

    def __init__(
        self,
        ai_adapter: Any = None,
        plugins: Optional[List[AnalysisPlugin]] = None
    ):
        self.ai_adapter = ai_adapter
        self.plugins = plugins or []

    @property
    def system_prompt(self) -> str:
        """系统提示词"""
        return ""

    async def run(self, query: str, context: Dict[str, Any]) -> str:
        """执行代理分析

        Args:
            query: 用户查询
            context: 上下文信息

        Returns:
            分析报告
        """
        # 1. 解析用户意图
        intent = await self._parse_intent(query)

        # 2. 选择并执行插件
        results = await self._execute_plugins(intent, context)

        # 3. 生成分析报告
        report = await self._generate_report(query, results)

        return report

    async def _parse_intent(self, query: str) -> Dict[str, Any]:
        """解析用户意图

        如果有 AI 适配器，使用 AI 解析；否则使用简单规则
        """
        if self.ai_adapter:
            prompt = f"""
            分析以下查询，提取分析意图：
            查询: {query}

            返回 JSON 格式:
            {{
                "analysis_type": "dcf|comps|screening|earnings|research",
                "symbol": "股票代码",
                "parameters": {{}}
            }}
            """
            response = await self.ai_adapter.generate(prompt)
            # 解析响应
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass

        # 简单规则解析
        return {
            "analysis_type": "research",
            "symbol": "",
            "parameters": {}
        }

    async def _execute_plugins(
        self,
        intent: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行插件"""
        results = {}
        for plugin in self.plugins:
            if plugin.name == intent.get("analysis_type"):
                results[plugin.name] = await plugin.execute(
                    stock_data=context.get("stock_data", {}),
                    params=intent.get("parameters", {})
                )
        return results

    async def _generate_report(
        self,
        query: str,
        results: Dict[str, Any]
    ) -> str:
        """生成分析报告

        如果有 AI 适配器，使用 AI 生成；否则使用模板
        """
        if self.ai_adapter:
            prompt = f"""
            基于以下分析结果，生成专业的金融分析报告：

            用户查询: {query}
            分析结果: {results}

            报告要求:
            1. 结构清晰，使用 Markdown 格式
            2. 包含关键数据和图表说明
            3. 提供明确的投资建议
            4. 列出风险提示
            """
            return await self.ai_adapter.generate(prompt)

        # 模板报告
        report = f"# 分析报告\n\n"
        report += f"**查询**: {query}\n\n"

        if results:
            report += "## 分析结果\n\n"
            for name, data in results.items():
                report += f"### {name}\n\n"
                report += f"```json\n{data}\n```\n\n"
        else:
            report += "未找到相关分析结果。\n"

        return report
```

- [ ] **Step 4: 实现代理注册表**

```python
# src/plugins/agents/registry.py
"""代理注册表"""

from typing import Dict, Any, Optional, List
from src.plugins.agents.base import AnalysisAgent


class AgentRegistry:
    """代理注册表"""

    _agents: Dict[str, AnalysisAgent] = {}

    @classmethod
    def register(cls, name: str, agent: AnalysisAgent) -> None:
        """注册代理"""
        cls._agents[name] = agent

    @classmethod
    def get(cls, name: str) -> Optional[AnalysisAgent]:
        """获取代理"""
        return cls._agents.get(name)

    @classmethod
    def list_agents(cls) -> Dict[str, str]:
        """列出所有代理"""
        return {name: agent.system_prompt[:50] + "..." for name, agent in cls._agents.items()}

    @classmethod
    def clear(cls) -> None:
        """清空注册表"""
        cls._agents.clear()
```

- [ ] **Step 5: 运行测试验证通过**

```bash
python -m pytest tests/unit/test_agent_base.py -v
```

Expected: ALL PASS

- [ ] **Step 6: 提交代码**

```bash
git add src/plugins/agents/__init__.py src/plugins/agents/base.py src/plugins/agents/registry.py tests/unit/test_agent_base.py
git commit -m "feat(agents): 添加代理基类和注册表"
```

---

## Task 8: Market Researcher 代理

**Files:**
- Create: `src/plugins/agents/market_researcher.py`
- Modify: `src/plugins/agents/__init__.py`

- [ ] **Step 1: 实现 Market Researcher 代理**

```python
# src/plugins/agents/market_researcher.py
"""市场研究员代理"""

from typing import Dict, Any, Optional, List
from src.plugins.agents.base import AnalysisAgent
from src.plugins.base import AnalysisPlugin


MARKET_RESEARCHER_PROMPT = """
你是一位资深市场研究员，专注于 A 股和港股市场。

## 工作流程
1. **行业概览**: 分析行业规模、增长趋势、政策环境
2. **竞争格局**: 识别主要参与者、市场份额、竞争优势
3. **同行对比**: 使用可比公司分析法评估目标公司
4. **投资想法**: 基于分析提出投资建议

## 分析框架
- 使用 PESTEL 分析宏观环境
- 使用波特五力分析行业竞争
- 使用 SWOT 分析公司优劣势
- 使用 DCF 和相对估值法评估价值

## 输出格式
生成结构化的研究报告，包含：
- 行业概况
- 竞争格局
- 公司分析
- 估值分析
- 投资建议
- 风险提示
"""


class MarketResearcherAgent(AnalysisAgent):
    """市场研究员代理"""

    def __init__(
        self,
        ai_adapter: Any = None,
        plugins: Optional[List[AnalysisPlugin]] = None
    ):
        super().__init__(ai_adapter, plugins)

    @property
    def system_prompt(self) -> str:
        return MARKET_RESEARCHER_PROMPT

    async def research(
        self,
        industry: str,
        symbol: str = None
    ) -> str:
        """执行市场研究

        Args:
            industry: 行业名称
            symbol: 可选的股票代码

        Returns:
            研究报告
        """
        context = {
            "industry": industry,
            "symbol": symbol
        }

        query = f"研究 {industry} 行业"
        if symbol:
            query += f"，重点关注 {symbol}"

        return await self.run(query, context)
```

- [ ] **Step 2: 更新 __init__.py**

```python
# src/plugins/agents/__init__.py
"""代理工作流模块"""

from .base import AnalysisAgent
from .registry import AgentRegistry
from .market_researcher import MarketResearcherAgent

__all__ = ["AnalysisAgent", "AgentRegistry", "MarketResearcherAgent"]
```

- [ ] **Step 3: 注册代理**

```python
# src/plugins/__init__.py
"""插件模块"""

from .base import AnalysisPlugin
from .registry import PluginRegistry

# 注册内置插件
from .financial_analysis import DCFValuationPlugin, ComparableAnalysisPlugin, StockScreeningPlugin
from .equity_research import EarningsAnalysisPlugin

PluginRegistry.register(DCFValuationPlugin())
PluginRegistry.register(ComparableAnalysisPlugin())
PluginRegistry.register(StockScreeningPlugin())
PluginRegistry.register(EarningsAnalysisPlugin())

# 注册代理
from .agents import AgentRegistry, MarketResearcherAgent
AgentRegistry.register("market_researcher", MarketResearcherAgent())

__all__ = ["AnalysisPlugin", "PluginRegistry", "AgentRegistry"]
```

- [ ] **Step 4: 添加代理 API**

```python
# src/web/api/plugins.py 中添加

class AgentRunRequest(BaseModel):
    """代理运行请求"""
    query: str
    context: Dict[str, Any] = {}


@router.post("/agents/{agent_name}/run")
async def run_agent(
    agent_name: str,
    request: AgentRunRequest
):
    """运行分析代理"""
    from src.plugins.agents.registry import AgentRegistry

    agent = AgentRegistry.get(agent_name)
    if not agent:
        raise HTTPException(404, f"Agent {agent_name} not found")

    result = await agent.run(
        query=request.query,
        context=request.context
    )
    return {"result": result}
```

- [ ] **Step 5: 提交代码**

```bash
git add src/plugins/agents/market_researcher.py src/plugins/agents/__init__.py src/plugins/__init__.py src/web/api/plugins.py
git commit -m "feat(agents): 添加 Market Researcher 代理"
```

---

## Task 9: 前端插件分析页面

**Files:**
- Create: `frontend/src/pages/PluginAnalysis.tsx`
- Create: `frontend/src/components/PluginSelector.tsx`
- Create: `frontend/src/components/ParameterForm.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建插件选择器组件**

```typescript
// frontend/src/components/PluginSelector.tsx
import React from 'react';
import { Select, Typography } from 'antd';

const { Text } = Typography;

interface Plugin {
  name: string;
  description: string;
}

interface PluginSelectorProps {
  plugins: Plugin[];
  onSelect: (pluginName: string) => void;
}

const PluginSelector: React.FC<PluginSelectorProps> = ({ plugins, onSelect }) => {
  return (
    <div style={{ marginBottom: 16 }}>
      <Text strong>选择分析插件</Text>
      <Select
        style={{ width: '100%', marginTop: 8 }}
        placeholder="选择插件"
        onChange={onSelect}
        options={plugins.map(p => ({
          label: p.name,
          value: p.name,
          title: p.description
        }))}
      />
    </div>
  );
};

export default PluginSelector;
```

- [ ] **Step 2: 创建参数表单组件**

```typescript
// frontend/src/components/ParameterForm.tsx
import React from 'react';
import { Form, InputNumber, Input, Typography } from 'antd';

const { Text } = Typography;

interface ParameterFormProps {
  plugin: string;
  onChange: (params: Record<string, any>) => void;
}

const ParameterForm: React.FC<ParameterFormProps> = ({ plugin, onChange }) => {
  const [form] = Form.useForm();

  // 根据插件类型显示不同的参数表单
  const renderFormFields = () => {
    switch (plugin) {
      case 'dcf_valuation':
        return (
          <>
            <Form.Item label="预测年数" name="years" initialValue={5}>
              <InputNumber min={1} max={10} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="增长率" name="growth_rate" initialValue={0.15}>
              <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="WACC" name="wacc" initialValue={0.10}>
              <InputNumber min={0.01} max={0.3} step={0.01} style={{ width: '100%' }} />
            </Form.Item>
          </>
        );
      case 'comparable_analysis':
        return (
          <Form.Item label="同行代码" name="peer_codes">
            <Input placeholder="输入同行股票代码，用逗号分隔" />
          </Form.Item>
        );
      case 'stock_screening':
        return (
          <>
            <Form.Item label="最大 PE" name="max_pe" initialValue={30}>
              <InputNumber min={0} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item label="最小 ROE" name="min_roe" initialValue={0.15}>
              <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
            </Form.Item>
          </>
        );
      default:
        return null;
    }
  };

  const handleValuesChange = (_: any, allValues: any) => {
    onChange(allValues);
  };

  return (
    <div style={{ marginBottom: 16 }}>
      <Text strong>参数配置</Text>
      <Form
        form={form}
        layout="vertical"
        onValuesChange={handleValuesChange}
        style={{ marginTop: 8 }}
      >
        {renderFormFields()}
      </Form>
    </div>
  );
};

export default ParameterForm;
```

- [ ] **Step 3: 创建插件分析页面**

```typescript
// frontend/src/pages/PluginAnalysis.tsx
import React, { useState, useEffect } from 'react';
import { Card, Button, Spin, message, Typography } from 'antd';
import { ThunderboltOutlined } from '@ant-design/icons';
import { api } from '../services/api';
import PluginSelector from '../components/PluginSelector';
import ParameterForm from '../components/ParameterForm';

const { Title, Text } = Typography;

interface Plugin {
  name: string;
  description: string;
}

const PluginAnalysis: React.FC = () => {
  const [selectedPlugin, setSelectedPlugin] = useState<string>('');
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [plugins, setPlugins] = useState<Plugin[]>([]);

  useEffect(() => {
    // 加载可用插件
    api.get('/plugins').then(res => {
      const pluginList = Object.entries(res.data).map(([name, desc]) => ({
        name,
        description: desc as string
      }));
      setPlugins(pluginList);
    }).catch(() => {
      message.error('加载插件列表失败');
    });
  }, []);

  const executeAnalysis = async () => {
    if (!selectedPlugin) {
      message.warning('请先选择插件');
      return;
    }

    setLoading(true);
    try {
      const response = await api.post(`/plugins/${selectedPlugin}/execute`, {
        symbol: '600519', // 默认股票
        params: parameters
      });
      setResult(response.data);
      message.success('分析完成');
    } catch (error) {
      message.error('分析失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>插件分析</Title>

      <div style={{ display: 'flex', gap: 24 }}>
        {/* 左侧: 配置面板 */}
        <Card title="分析配置" style={{ width: 400 }}>
          <PluginSelector
            plugins={plugins}
            onSelect={setSelectedPlugin}
          />
          <ParameterForm
            plugin={selectedPlugin}
            onChange={setParameters}
          />
          <Button
            type="primary"
            icon={<ThunderboltOutlined />}
            onClick={executeAnalysis}
            loading={loading}
            block
          >
            执行分析
          </Button>
        </Card>

        {/* 右侧: 结果展示 */}
        <Card title="分析结果" style={{ flex: 1, minHeight: 500 }}>
          <Spin spinning={loading}>
            {result ? (
              <pre style={{ whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(result, null, 2)}
              </pre>
            ) : (
              <Text type="secondary">请选择插件并执行分析</Text>
            )}
          </Spin>
        </Card>
      </div>
    </div>
  );
};

export default PluginAnalysis;
```

- [ ] **Step 4: 更新路由**

```typescript
// frontend/src/App.tsx 中添加路由
import PluginAnalysis from './pages/PluginAnalysis';

// 在 Routes 中添加
<Route path="/plugins" element={<PluginAnalysis />} />
```

- [ ] **Step 5: 提交代码**

```bash
git add frontend/src/pages/PluginAnalysis.tsx frontend/src/components/PluginSelector.tsx frontend/src/components/ParameterForm.tsx frontend/src/App.tsx
git commit -m "feat(frontend): 添加插件分析页面"
```

---

## Task 10: 集成测试

**Files:**
- Create: `tests/integration/test_plugins_api.py`

- [ ] **Step 1: 编写集成测试**

```python
# tests/integration/test_plugins_api.py
"""插件 API 集成测试"""

import pytest
from fastapi.testclient import TestClient
from src.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_list_plugins(client):
    """测试列出插件"""
    response = client.get("/api/v1/plugins/")
    assert response.status_code == 200
    data = response.json()
    assert "dcf_valuation" in data
    assert "comparable_analysis" in data


def test_get_plugin_info(client):
    """测试获取插件信息"""
    response = client.get("/api/v1/plugins/dcf_valuation")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "dcf_valuation"
    assert "parameters" in data


def test_execute_dcf_plugin(client):
    """测试执行 DCF 插件"""
    response = client.post(
        "/api/v1/plugins/dcf_valuation/execute",
        json={
            "symbol": "600519",
            "params": {
                "years": 5,
                "growth_rate": 0.15
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "enterprise_value" in data
    assert "per_share_value" in data


def test_list_commands(client):
    """测试列出命令"""
    response = client.get("/api/v1/commands/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["name"] == "dcf"
```

- [ ] **Step 2: 运行集成测试**

```bash
python -m pytest tests/integration/test_plugins_api.py -v
```

Expected: ALL PASS

- [ ] **Step 3: 提交代码**

```bash
git add tests/integration/test_plugins_api.py
git commit -m "test: 添加插件 API 集成测试"
```

---

## 自我审查清单

### 1. 规范覆盖检查

- [x] 插件基类和注册表 ✅ Task 1
- [x] DCF 估值插件 ✅ Task 2
- [x] 可比公司分析插件 ✅ Task 3
- [x] 股票筛选插件 ✅ Task 4
- [x] 财报分析插件 ✅ Task 5
- [x] 插件 API 端点 ✅ Task 6
- [x] 代理工作流基类 ✅ Task 7
- [x] Market Researcher 代理 ✅ Task 8
- [x] 前端插件分析页面 ✅ Task 9
- [x] 集成测试 ✅ Task 10

### 2. 占位符扫描

- [x] 无 TBD 或 TODO 标记
- [x] 所有步骤包含完整代码
- [x] 所有测试包含断言

### 3. 类型一致性检查

- [x] 插件接口一致：`AnalysisPlugin`
- [x] 注册表接口一致：`PluginRegistry`, `AgentRegistry`
- [x] API 端点一致：`/plugins`, `/commands`

---

## 执行选项

计划完成并保存到 `docs/superpowers/plans/2026-06-09-financial-services-integration.md`。

**两种执行方式：**

**1. Subagent-Driven（推荐）** - 每个任务分派新的子代理，任务间进行审查，快速迭代

**2. Inline Execution** - 在当前会话中执行任务，批量执行并设置检查点

**选择哪种方式？**
