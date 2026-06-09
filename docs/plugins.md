# Stock-Hub 插件系统文档

## 概述

Stock-Hub 插件系统提供模块化的金融分析能力，支持多种估值模型、技术指标分析和 AI 代理工作流。插件系统由三个核心部分组成：

- **分析插件 (AnalysisPlugin)** -- 独立的金融分析模块，每个插件实现特定的分析逻辑
- **分析代理 (AnalysisAgent)** -- AI 驱动的分析工作流，协调多个插件完成复杂分析任务
- **注册表 (Registry)** -- 统一管理插件和代理的注册、发现与调用

## 插件列表

### 金融分析插件

| 插件名称 | 类 | 功能 | 核心参数 |
|----------|------|------|----------|
| `dcf_valuation` | `DCFValuationPlugin` | DCF 现金流折现估值 | years, growth_rate, terminal_growth, wacc |
| `comparable_analysis` | `ComparableAnalysisPlugin` | 可比公司估值分析 | peer_codes, metrics |
| `stock_screening` | `StockScreeningPlugin` | 多维度股票筛选 | universe, filters, sort_by, limit |
| `lbo_analysis` | `LBOAnalysisPlugin` | LBO 杠杆收购模型 | purchase_price, debt_ratio, interest_rate, exit_multiple, holding_period |
| `ddm_valuation` | `DDMValuationPlugin` | DDM 股息贴现模型 | dividend_per_share, growth_rate, required_return, years |
| `merger_analysis` | `MergerAnalysisPlugin` | 并购分析 | acquirer_symbol, target_symbol, deal_price, synergy_revenue, synergy_cost |
| `comprehensive_analysis` | `ComprehensiveAnalysisPlugin` | 综合分析（100分评分系统） | symbol, days |

### 股票研究插件

| 插件名称 | 类 | 功能 | 核心参数 |
|----------|------|------|----------|
| `earnings_analysis` | `EarningsAnalysisPlugin` | 财报分析 | period, compare_with, focus_areas |
| `company_one_pager` | `OnePagerPlugin` | 公司一页纸概述 | symbol, include_financials, include_peers |

## 使用方法

### API 调用

插件 API 路由前缀为 `/api/v1/plugins`。

#### 列出所有插件

```bash
GET /api/v1/plugins/
```

返回 `{插件名称: 插件描述}` 的字典。

#### 获取插件详情

```bash
GET /api/v1/plugins/{plugin_name}
```

返回插件的名称、描述、版本和参数定义。

#### 执行插件分析

```bash
POST /api/v1/plugins/{plugin_name}/execute
Content-Type: application/json

{
  "symbol": "600519",
  "params": {
    "years": 5,
    "growth_rate": 0.15
  }
}
```

请求体使用 `PluginExecuteRequest` 模型：
- `symbol` (str, 必填) -- 股票代码
- `params` (dict, 可选) -- 插件参数，不同插件接受不同参数
- `period` (str, 可选) -- 分析期间

#### 导出分析结果

```bash
GET /api/v1/plugins/{plugin_name}/export?symbol=600519&format=json
```

支持 `json` 和 `csv` 两种格式，返回文件下载响应。

### 前端使用

1. 访问前端页面，进入"插件分析"页面
2. 在斜杠命令输入框中输入命令，或从下拉列表选择插件
3. 输入股票代码
4. 填写插件参数
5. 点击"执行分析"
6. 查看结果，支持导出 JSON/CSV

### 斜杠命令

前端支持通过斜杠命令快速执行插件分析：

| 命令 | 功能 |
|------|------|
| `/dcf <股票代码>` | DCF 估值分析 |
| `/comps <股票代码> <同行代码>` | 可比公司分析 |
| `/screen <筛选条件>` | 股票筛选 |
| `/earnings <股票代码> <期间>` | 财报分析 |
| `/lbo <股票代码>` | LBO 杠杆收购分析 |
| `/ddm <股票代码>` | DDM 股息贴现估值 |
| `/onepager <股票代码>` | 公司一页纸概述 |

## 各插件参数详解

### DCF 估值 (`dcf_valuation`)

现金流折现模型，通过预测未来自由现金流并折现来估算企业内在价值。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| years | int | 5 | 预测年数 |
| growth_rate | float | 0.15 | 前N年自由现金流年增长率 |
| terminal_growth | float | 0.03 | 永续增长率（终值增长率） |
| wacc | float | 0.10 | 加权平均资本成本（折现率） |

返回字段：`enterprise_value`, `equity_value`, `per_share_value`, `current_price`, `upside_pct`, `cash_flows`, `terminal_value`, `pv_cash_flows`, `pv_terminal_value`

### 可比公司分析 (`comparable_analysis`)

通过同行业公司的估值指标对比，评估目标公司相对估值水平。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| peer_codes | List[str] | [] | 同行公司股票代码列表 |
| metrics | List[str] | ["PE", "PB", "PS", "EV/EBITDA"] | 比较的估值指标 |

返回字段：`target_valuation`, `peer_comparison`, `avg_peer_metrics`, `implied_value`, `avg_implied_value`, `premium_discount`, `overall_premium_discount_pct`

### 股票筛选 (`stock_screening`)

基于多维度财务指标筛选股票池，支持自定义条件和综合评分排序。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| universe | str | "hs300" | 股票池名称 |
| filters | Dict | {} | 筛选条件，格式: `{指标名: {min: ..., max: ...}}` |
| sort_by | str | "score" | 排序字段 |
| limit | int | 10 | 返回结果数量上限 |

返回字段：`results`, `total_count`, `filters_applied`

### LBO 杠杆收购 (`lbo_analysis`)

通过杠杆收购模型计算投资回报率、MOIC、债务偿还等关键指标。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| purchase_price | float | 0 | 收购价格（元），0 表示使用当前市值 |
| debt_ratio | float | 0.60 | 债务占比（0-1） |
| interest_rate | float | 0.05 | 债务年利率 |
| exit_multiple | float | 10.0 | 退出时 EV/EBITDA 倍数 |
| holding_period | int | 5 | 持有期（年） |

返回字段：`purchase_price`, `equity_invested`, `debt_at_entry`, `moic`, `equity_irr_pct`, `debt_paydown`, `remaining_debt`, `yearly_projections`

### DDM 股息贴现 (`ddm_valuation`)

通过预测未来股息并折现来估算股票内在价值。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| dividend_per_share | float | 0 | 每股股息（元） |
| growth_rate | float | 0.05 | 股息年增长率 |
| required_return | float | 0.10 | 投资者要求回报率（折现率） |
| years | int | 10 | 预测年数 |

返回字段：`intrinsic_value`, `current_price`, `upside_pct`, `dividend_yield_pct`, `pv_dividends`, `terminal_value`, `dividend_projections`

### 并购分析 (`merger_analysis`)

评估并购交易的合理性、协同效应和估值。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| acquirer_symbol | str | -- | 收购方股票代码 |
| target_symbol | str | -- | 目标公司股票代码 |
| deal_price | float | -- | 交易价格（亿元） |
| synergy_revenue | float | 0.0 | 预期收入协同效应（亿元） |
| synergy_cost | float | 0.0 | 预期成本协同效应（亿元） |

返回字段：`valuation`, `synergy`, `eps_impact`, `highlights`, `risks`, `recommendation`

### 综合分析 (`comprehensive_analysis`)

100分评分系统，包含 MA/MACD/RSI/量能/乖离率/支撑位 6 维度分析。支持 A 股、港股、美股。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| symbol | str | -- | 股票代码 |
| days | int | 120 | 历史天数 |

返回字段：`indicators` (ma, macd, rsi, volume, bias, support), `trend_score`, `signal`, `signal_cn`

### 财报分析 (`earnings_analysis`)

分析公司财报关键指标，识别亮点与风险，生成结构化分析报告。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| period | str | "" | 分析期间，如 "2024Q3" |
| compare_with | str | "" | 对比期间，如 "2023Q3" |
| focus_areas | List[str] | [] | 重点关注领域，如 ["revenue", "margins", "cash_flow"] |

返回字段：`summary`, `highlights`, `risks`, `financial_metrics`, `yoy_comparison`

### 公司一页纸 (`company_one_pager`)

生成公司概况、业务描述、财务摘要、估值和风险的一页纸报告。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| symbol | str | "" | 股票代码 |
| include_financials | bool | true | 是否包含财务摘要 |
| include_peers | bool | false | 是否包含同行业对比 |

返回字段：`overview`, `business`, `financial_summary`, `valuation`, `risks`

## 代理系统

代理 (AnalysisAgent) 封装复杂的分析工作流，协调多个插件和 AI 适配器完成分析任务。

### 代理列表

| 代理名称 | 类 | 功能 | 核心方法 |
|----------|------|------|----------|
| `market_researcher` | `MarketResearcherAgent` | 市场研究员 | `research(industry, symbol)` |
| `earnings_reviewer` | `EarningsReviewerAgent` | 财报分析师 | `analyze(symbol, period)` |
| `portfolio_manager` | `PortfolioManagerAgent` | 投资组合经理 | `analyze_portfolio(holdings, risk_profile)`, `suggest_allocation(total_capital, risk_profile)` |
| `risk_manager` | `RiskManagerAgent` | 风险管理专家 | `assess_portfolio_risk(holdings, confidence_level)`, `stress_test(holdings, scenarios)` |

### 代理工作流

代理默认执行三步工作流：

1. **解析意图** -- `_parse_intent()` 解析用户查询，确定需要调用的插件
2. **执行插件** -- `_execute_plugins()` 调用关联的分析插件获取数据
3. **生成报告** -- `_generate_report()` 汇总插件结果，生成分析报告

### API 调用

```bash
POST /api/v1/plugins/agents/{agent_name}/run
Content-Type: application/json

{
  "query": "研究白酒行业",
  "context": {
    "industry": "白酒",
    "symbol": "600519"
  }
}
```

请求体使用 `AgentRunRequest` 模型：
- `query` (str, 必填) -- 分析查询
- `context` (dict, 可选) -- 额外上下文信息

## 开发指南

### 创建新插件

1. 在 `src/plugins/financial_analysis/` 或 `src/plugins/equity_research/` 下创建新文件
2. 继承 `AnalysisPlugin` 基类
3. 实现必需的抽象属性和方法
4. 在 `src/plugins/__init__.py` 中注册插件

```python
from typing import Dict, Any
from src.plugins.base import AnalysisPlugin


class MyPlugin(AnalysisPlugin):
    """我的自定义插件"""

    @property
    def name(self) -> str:
        return "my_plugin"

    @property
    def description(self) -> str:
        return "我的自定义插件描述"

    def get_parameters(self) -> Dict[str, Any]:
        return {
            "param1": {
                "type": "str",
                "default": "",
                "description": "参数1说明"
            },
            "param2": {
                "type": "int",
                "default": 10,
                "description": "参数2说明"
            },
        }

    async def execute(
        self,
        stock_data: Any,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行分析

        Args:
            stock_data: 股票数据字典
            params: 插件参数

        Returns:
            分析结果字典
        """
        # 实现分析逻辑
        return {"result": "success"}
```

注册插件（在 `src/plugins/__init__.py` 中添加）：

```python
from .financial_analysis.my_plugin import MyPlugin
PluginRegistry.register(MyPlugin())
```

### 创建新代理

1. 在 `src/plugins/agents/` 下创建新文件
2. 继承 `AnalysisAgent` 基类
3. 实现 `system_prompt` 属性
4. 添加业务方法
5. 在 `src/plugins/__init__.py` 中注册代理

```python
from typing import Any, Dict, List, Optional
from src.plugins.agents.base import AnalysisAgent
from src.plugins.base import AnalysisPlugin


MY_AGENT_PROMPT = """
你是一位专业的...分析专家。

## 工作流程
1. ...
2. ...
"""


class MyAgent(AnalysisAgent):
    """我的自定义代理"""

    def __init__(
        self,
        ai_adapter: Any = None,
        plugins: Optional[List[AnalysisPlugin]] = None,
    ):
        super().__init__(ai_adapter, plugins)

    @property
    def system_prompt(self) -> str:
        return MY_AGENT_PROMPT

    async def my_method(self, param1: str) -> Dict[str, Any]:
        """自定义分析方法"""
        context = {"param1": param1}
        return await self.run(f"执行 {param1} 分析", context)
```

注册代理（在 `src/plugins/__init__.py` 中添加）：

```python
from .agents.my_agent import MyAgent
AgentRegistry.register("my_agent", MyAgent)
```

## 缓存机制

插件系统内置缓存支持，默认 TTL 为 300 秒。

### 自动缓存

`AnalysisPlugin.safe_execute()` 方法自动处理缓存和错误处理：

```python
# 通过 safe_execute 调用，自动启用缓存（默认 300 秒）
result = await plugin.safe_execute(stock_data, params, cache_ttl=600)
```

### 装饰器缓存

使用 `@cached` 装饰器为自定义函数添加缓存：

```python
from src.plugins.cache import cached

@cached(ttl=600)
async def my_expensive_function(param1, param2):
    # 缓存 600 秒
    return result
```

### 缓存管理

```python
from src.plugins.cache import plugin_cache

# 清空所有缓存
plugin_cache.clear()
```

## 错误处理

插件系统定义了分层的错误类型：

| 错误类 | 说明 |
|--------|------|
| `PluginError` | 插件错误基类 |
| `DataNotFoundError` | 数据未找到 |
| `InvalidParameterError` | 无效参数 |
| `CalculationError` | 计算错误 |

### 错误处理示例

```python
from src.plugins.errors import PluginError, handle_plugin_error

try:
    result = await plugin.execute(stock_data, params)
except PluginError as e:
    error_result = handle_plugin_error(e, plugin.name, params)
    # error_result 包含: error, error_type, error_message, plugin
```

`safe_execute()` 方法内置错误处理，异常时返回包含错误信息的字典而非抛出异常。

## 结果导出

使用 `ResultExporter` 将分析结果导出为不同格式：

```python
from src.plugins.export import ResultExporter

# 导出为 JSON
json_str = ResultExporter.to_json(result, pretty=True)

# 导出为 CSV（自动扁平化嵌套结构）
csv_str = ResultExporter.to_csv(result)

# 生成导出文件名
filename = ResultExporter.get_export_filename("dcf_valuation", "600519", "json")
# 格式: dcf_valuation_600519_20260609_120000.json
```

## 项目结构

```
src/plugins/
    __init__.py              # 插件和代理注册
    base.py                  # AnalysisPlugin 基类
    registry.py              # PluginRegistry 注册表
    cache.py                 # PluginCache 缓存工具
    errors.py                # 错误类型定义
    export.py                # ResultExporter 结果导出
    financial_analysis/
        __init__.py
        dcf.py               # DCF 估值插件
        comps.py             # 可比公司分析插件
        screening.py         # 股票筛选插件
        lbo.py               # LBO 杠杆收购插件
        ddm.py               # DDM 股息贴现插件
        merger.py            # 并购分析插件
        comprehensive_analysis.py  # 综合分析插件
        technical_indicators.py    # 技术指标计算
    equity_research/
        __init__.py
        earnings.py          # 财报分析插件
        one_pager.py         # 公司一页纸插件
    agents/
        __init__.py
        base.py              # AnalysisAgent 基类
        registry.py          # AgentRegistry 注册表
        market_researcher.py # 市场研究员代理
        earnings_reviewer.py # 财报分析师代理
        portfolio_manager.py # 投资组合经理代理
        risk_manager.py      # 风险管理专家代理
```
