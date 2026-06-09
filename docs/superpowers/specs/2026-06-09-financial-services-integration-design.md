# Financial Services 集成设计文档

**日期**: 2026-06-09
**状态**: 设计完成，待实现
**作者**: Claude + 用户协作

---

## 1. 概述

### 1.1 项目背景

stock-hub 是一个 A 股量化交易一体化平台，目前支持多数据源接入、10+ 分析策略、5 种 AI 适配器。为了增强专业金融分析能力，需要集成 `anthropics/financial-services` 项目中的分析技能、代理工作流和数据连接器架构。

### 1.2 集成目标

将 `financial-services` 项目的专业金融分析能力移植到 stock-hub，包括：
- **核心分析技能**: DCF 估值、可比公司分析、LBO 模型、股票筛选、财报分析
- **代理工作流**: Market Researcher、Earnings Reviewer
- **数据连接器架构**: MCP 连接器模式，适配 A 股/港股数据源
- **前端集成**: 斜杠命令系统、分析结果可视化

### 1.3 目标市场

- **主要**: A 股市场
- **扩展**: 港股市场

---

## 2. 架构设计

### 2.1 模块化插件架构

采用模块化插件架构，每个分析技能作为独立插件，通过注册机制与现有分析服务集成。

```
src/plugins/
├── __init__.py
├── base.py              # 插件基类
├── registry.py          # 插件注册表
├── financial_analysis/  # 核心金融分析插件
│   ├── __init__.py
│   ├── dcf.py           # DCF 估值
│   ├── comps.py         # 可比公司分析
│   ├── lbo.py           # LBO 模型
│   └── screening.py     # 股票筛选
├── equity_research/     # 股票研究插件
│   ├── __init__.py
│   ├── earnings.py      # 财报分析
│   ├── model_update.py  # 模型更新
│   └── one_pager.py     # 公司简介
└── agents/              # 代理工作流
    ├── __init__.py
    ├── base.py          # 代理基类
    ├── market_researcher.py
    └── earnings_reviewer.py
```

### 2.2 插件基类设计

```python
# src/plugins/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.data.models import StockData

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
        stock_data: StockData,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行分析"""
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """获取参数定义"""
        pass
```

### 2.3 插件注册表

```python
# src/plugins/registry.py
from typing import Dict, Any, Optional, List
from src.plugins.base import AnalysisPlugin

class PluginRegistry:
    """插件注册表"""

    _plugins: Dict[str, AnalysisPlugin] = {}

    @classmethod
    def register(cls, plugin: AnalysisPlugin):
        """注册插件"""
        cls._plugins[plugin.name] = plugin

    @classmethod
    def get(cls, name: str) -> Optional[AnalysisPlugin]:
        """获取插件"""
        return cls._plugins.get(name)

    @classmethod
    def list_plugins(cls) -> Dict[str, str]:
        """列出所有插件"""
        return {name: p.description for name, p in cls._plugins.items()}

    @classmethod
    def get_all(cls) -> List[AnalysisPlugin]:
        """获取所有插件"""
        return list(cls._plugins.values())
```

---

## 3. 核心分析插件

### 3.1 DCF 估值插件

**来源**: `financial-services/plugins/vertical-plugins/financial-analysis/skills/dcf/`

**功能**: 现金流折现估值模型，计算企业价值和每股价值

**参数定义**:
```python
{
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
```

**输出结构**:
```python
{
    "enterprise_value": float,      # 企业价值
    "equity_value": float,          # 股权价值
    "per_share_value": float,       # 每股价值
    "current_price": float,         # 当前价格
    "upside_pct": float,            # 上行空间百分比
    "sensitivity_table": Dict,      # 敏感性分析表
    "assumptions": Dict,            # 假设条件
    "cash_flows": List[Dict]        # 现金流明细
}
```

**实现逻辑**:
1. 获取历史财务数据（收入、利润、现金流）
2. 预测未来 N 年现金流
3. 计算终值
4. 折现计算企业价值
5. 计算股权价值和每股价值
6. 生成敏感性分析表

### 3.2 可比公司分析插件

**来源**: `financial-services/plugins/vertical-plugins/financial-analysis/skills/comps/`

**功能**: 通过同行业公司对比估值

**参数定义**:
```python
{
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
```

**输出结构**:
```python
{
    "target_valuation": Dict,       # 目标公司估值
    "peer_comparison": List[Dict],  # 同行对比数据
    "implied_value": float,         # 隐含价值
    "premium_discount": float       # 溢价/折价百分比
}
```

**实现逻辑**:
1. 获取目标公司财务数据
2. 获取同行公司财务数据
3. 计算各估值指标
4. 计算隐含价值
5. 生成对比报告

### 3.3 股票筛选插件

**来源**: `financial-services/plugins/vertical-plugins/financial-analysis/skills/screen/`

**功能**: 基于多维度指标筛选股票

**参数定义**:
```python
{
    "universe": {
        "type": "str",
        "default": "hs300",
        "description": "股票池"
    },
    "filters": {
        "type": "Dict[str, Dict]",
        "description": "筛选条件"
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
```

**输出结构**:
```python
{
    "results": List[Dict],          # 筛选结果
    "total_count": int,             # 总数
    "filters_applied": Dict         # 应用的筛选条件
}
```

### 3.4 财报分析插件

**来源**: `financial-services/plugins/vertical-plugins/equity-research/skills/earnings/`

**功能**: 分析公司财报，生成分析报告

**参数定义**:
```python
{
    "symbol": {
        "type": "str",
        "description": "股票代码"
    },
    "period": {
        "type": "str",
        "description": "财报期间"
    },
    "compare_with": {
        "type": "str",
        "description": "对比期间"
    },
    "focus_areas": {
        "type": "List[str]",
        "default": ["revenue", "margins", "cash_flow"],
        "description": "关注领域"
    }
}
```

**输出结构**:
```python
{
    "summary": str,                 # 财报摘要
    "highlights": List[str],        # 亮点
    "risks": List[str],             # 风险
    "financial_metrics": Dict,      # 财务指标
    "yoy_comparison": Dict          # 同比对比
}
```

---

## 4. 代理工作流

### 4.1 代理基类

```python
# src/plugins/agents/base.py
from typing import Dict, Any, List
from src.ai.base import AIAdapter
from src.plugins.base import AnalysisPlugin

class AnalysisAgent:
    """分析代理基类"""

    def __init__(self, ai_adapter: AIAdapter, plugins: List[AnalysisPlugin]):
        self.ai_adapter = ai_adapter
        self.plugins = plugins

    @property
    def system_prompt(self) -> str:
        """系统提示词"""
        return ""

    async def run(self, query: str, context: Dict[str, Any]) -> str:
        """执行代理分析"""
        # 1. 解析用户意图
        intent = await self._parse_intent(query)

        # 2. 选择并执行插件
        results = await self._execute_plugins(intent, context)

        # 3. 生成分析报告
        report = await self._generate_report(query, results)

        return report

    async def _parse_intent(self, query: str) -> Dict[str, Any]:
        """解析用户意图"""
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
        return await self.ai_adapter.generate(prompt)

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
                    stock_data=context.get("stock_data"),
                    params=intent.get("parameters", {})
                )
        return results

    async def _generate_report(
        self,
        query: str,
        results: Dict[str, Any]
    ) -> str:
        """生成分析报告"""
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
```

### 4.2 Market Researcher 代理

```python
# src/plugins/agents/market_researcher.py
from src.plugins.agents.base import AnalysisAgent

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

    @property
    def system_prompt(self) -> str:
        return MARKET_RESEARCHER_PROMPT

    async def research(self, industry: str, symbol: str = None) -> str:
        """执行市场研究"""
        context = {
            "industry": industry,
            "symbol": symbol
        }
        return await self.run(
            f"研究 {industry} 行业" + (f"，重点关注 {symbol}" if symbol else ""),
            context
        )
```

### 4.3 Earnings Reviewer 代理

```python
# src/plugins/agents/earnings_reviewer.py
from src.plugins.agents.base import AnalysisAgent

EARNINGS_REVIEWER_PROMPT = """
你是一位专业的财报分析师，专注于 A 股和港股公司财报分析。

## 工作流程
1. **获取财报**: 获取最新财报数据
2. **指标分析**: 分析关键财务指标变化
3. **对比分析**: 与历史数据和预期对比
4. **生成报告**: 生成研报草稿

## 分析重点
- 收入增长趋势
- 毛利率和净利率变化
- 现金流状况
- 资产负债表健康度
- 管理层展望

## 输出格式
生成结构化的财报分析报告，包含：
- 财报摘要
- 关键指标分析
- 同比/环比对比
- 投资建议
- 风险提示
"""

class EarningsReviewerAgent(AnalysisAgent):
    """财报分析代理"""

    @property
    def system_prompt(self) -> str:
        return EARNINGS_REVIEWER_PROMPT

    async def analyze(self, symbol: str, period: str) -> str:
        """分析财报"""
        context = {
            "symbol": symbol,
            "period": period
        }
        return await self.run(
            f"分析 {symbol} {period} 财报",
            context
        )
```

---

## 5. 数据连接器架构

### 5.1 连接器基类

```python
# src/data/connectors/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class DataConnector(ABC):
    """数据连接器基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """连接器名称"""
        pass

    @property
    @abstractmethod
    def capabilities(self) -> List[str]:
        """支持的数据类型"""
        pass

    @abstractmethod
    async def connect(self, config: Dict[str, Any]) -> bool:
        """建立连接"""
        pass

    @abstractmethod
    async def fetch(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """获取数据"""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
```

### 5.2 预定义连接器

| 连接器 | 数据源 | 能力 | 状态 |
|--------|--------|------|------|
| AkShareConnector | AkShare | A 股行情、财务数据 | ✅ 已实现 |
| WestockConnector | westock-data-skillhub | 搜索、K 线、技术指标 | ✅ 已实现 |
| AShareSkillConnector | a-share-skill | 实时行情、历史数据 | ✅ 已实现 |
| TushareConnector | Tushare | A 股全面数据 | 🔜 待实现 |
| YFinanceConnector | yfinance | 港股、美股数据 | 🔜 待实现 |
| HKStockConnector | yfinance/AkShare | 港股行情、财务数据 | 🔜 待实现 |

### 5.3 连接器注册表

```python
# src/data/connectors/registry.py
from typing import Dict, Any, List, Optional
from src.data.connectors.base import DataConnector

class ConnectorRegistry:
    """连接器注册表"""

    _connectors: Dict[str, DataConnector] = {}

    @classmethod
    def register(cls, connector: DataConnector):
        """注册连接器"""
        cls._connectors[connector.name] = connector

    @classmethod
    def get(cls, name: str) -> Optional[DataConnector]:
        """获取连接器"""
        return cls._connectors.get(name)

    @classmethod
    def get_by_capability(cls, capability: str) -> List[DataConnector]:
        """根据能力获取连接器"""
        return [
            c for c in cls._connectors.values()
            if capability in c.capabilities
        ]

    @classmethod
    def list_connectors(cls) -> Dict[str, List[str]]:
        """列出所有连接器"""
        return {
            name: c.capabilities
            for name, c in cls._connectors.items()
        }
```

### 5.4 港股数据连接器

```python
# src/data/connectors/hk_stock_connector.py
from typing import Dict, Any, List
import yfinance as yf
from src.data.connectors.base import DataConnector

class HKStockConnector(DataConnector):
    """港股数据连接器"""

    @property
    def name(self) -> str:
        return "hk_stock"

    @property
    def capabilities(self) -> List[str]:
        return ["hk_quote", "hk_kline", "hk_financial"]

    async def connect(self, config: Dict[str, Any]) -> bool:
        """建立连接"""
        # yfinance 不需要显式连接
        return True

    async def fetch(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """获取港股数据"""
        symbol = query.get("symbol")
        data_type = query.get("type")

        # 转换股票代码格式 (如 0700.HK)
        yf_symbol = self._convert_symbol(symbol)

        if data_type == "quote":
            return await self._fetch_quote(yf_symbol)
        elif data_type == "kline":
            return await self._fetch_kline(yf_symbol, query)
        elif data_type == "financial":
            return await self._fetch_financial(yf_symbol)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")

    async def disconnect(self) -> None:
        """断开连接"""
        pass

    def _convert_symbol(self, symbol: str) -> str:
        """转换股票代码格式"""
        # 0700 -> 0700.HK
        if not symbol.endswith(".HK"):
            return f"{symbol}.HK"
        return symbol

    async def _fetch_quote(self, symbol: str) -> Dict[str, Any]:
        """获取实时行情"""
        ticker = yf.Ticker(symbol)
        info = ticker.info
        return {
            "symbol": symbol,
            "price": info.get("currentPrice"),
            "change": info.get("regularMarketChange"),
            "change_pct": info.get("regularMarketChangePercent"),
            "volume": info.get("volume"),
            "market_cap": info.get("marketCap")
        }

    async def _fetch_kline(
        self,
        symbol: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取 K 线数据"""
        ticker = yf.Ticker(symbol)
        period = params.get("period", "1y")
        interval = params.get("interval", "1d")
        df = ticker.history(period=period, interval=interval)
        return df.to_dict(orient="records")

    async def _fetch_financial(self, symbol: str) -> Dict[str, Any]:
        """获取财务数据

        输出格式:
        {
            "income_stmt": {
                "2024-12-31": {
                    "Total Revenue": 1000000000,
                    "Net Income": 200000000,
                    ...
                },
                ...
            },
            "balance_sheet": {
                "2024-12-31": {
                    "Total Assets": 5000000000,
                    "Total Liabilities": 2000000000,
                    ...
                },
                ...
            },
            "cashflow": {
                "2024-12-31": {
                    "Operating Cash Flow": 300000000,
                    "Capital Expenditure": -50000000,
                    ...
                },
                ...
            }
        }
        """
        ticker = yf.Ticker(symbol)
        return {
            "income_stmt": ticker.income_stmt.to_dict(),
            "balance_sheet": ticker.balance_sheet.to_dict(),
            "cashflow": ticker.cashflow.to_dict()
        }
```

---

## 6. 前端集成

### 6.1 斜杠命令系统

**新增命令**:
| 命令 | 功能 | 插件 |
|------|------|------|
| `/dcf` | DCF 估值 | dcf_valuation |
| `/comps` | 可比公司分析 | comparable_analysis |
| `/screen` | 股票筛选 | stock_screening |
| `/earnings` | 财报分析 | earnings_analysis |
| `/one-pager` | 公司简介 | company_one_pager |
| `/research` | 市场研究 | market_researcher |

**前端组件**:
```typescript
// frontend/src/components/SlashCommand.tsx
import React, { useState, useEffect } from 'react';
import { Input, List, Tag } from 'antd';
import { api } from '../services/api';

interface Command {
  name: string;
  description: string;
  plugin: string;
  usage: string;
}

const SlashCommand: React.FC = () => {
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<Command[]>([]);
  const [commands, setCommands] = useState<Command[]>([]);

  useEffect(() => {
    // 加载可用命令
    api.get('/plugins/commands').then(res => {
      setCommands(res.data);
    });
  }, []);

  const handleInputChange = (value: string) => {
    setQuery(value);
    if (value.startsWith('/')) {
      const command = value.slice(1).split(' ')[0];
      const matchingCommands = commands.filter(c =>
        c.name.startsWith(command)
      );
      setSuggestions(matchingCommands);
    } else {
      setSuggestions([]);
    }
  };

  const handleCommandSelect = async (command: Command) => {
    const args = query.slice(command.name.length + 2).trim();

    // 解析参数，支持引号包裹的参数
    const parseArgs = (argStr: string): { symbol: string; params: Record<string, any> } => {
      const parts = argStr.match(/(?:[^\s"]+|"[^"]*")+/g) || [];
      const symbol = parts[0] || '';
      const params: Record<string, any> = {};

      // 解析 key=value 格式的参数
      for (let i = 1; i < parts.length; i++) {
        const [key, value] = parts[i].split('=');
        if (key && value) {
          params[key] = value.replace(/"/g, '');
        }
      }

      return { symbol, params };
    };

    const { symbol, params } = parseArgs(args);
    const result = await api.post(`/plugins/${command.plugin}/execute`, {
      symbol,
      params
    });
    // 显示结果
    showAnalysisResult(result.data);
  };

  return (
    <div className="slash-command">
      <Input
        prefix="/"
        placeholder="输入命令... (如 /dcf 600519)"
        value={query}
        onChange={e => handleInputChange(e.target.value)}
        onPressEnter={() => {
          if (suggestions.length > 0) {
            handleCommandSelect(suggestions[0]);
          }
        }}
      />
      {suggestions.length > 0 && (
        <List
          className="command-suggestions"
          dataSource={suggestions}
          renderItem={item => (
            <List.Item onClick={() => handleCommandSelect(item)}>
              <Tag color="blue">/{item.name}</Tag>
              <span>{item.description}</span>
            </List.Item>
          )}
        />
      )}
    </div>
  );
};

export default SlashCommand;
```

### 6.2 插件分析页面

```typescript
// frontend/src/pages/PluginAnalysis.tsx
import React, { useState, useEffect } from 'react';
import { Card, Select, Form, Button, Spin } from 'antd';
import { api } from '../services/api';
import PluginSelector from '../components/PluginSelector';
import ParameterForm from '../components/ParameterForm';
import AnalysisResult from '../components/AnalysisResult';

const PluginAnalysis: React.FC = () => {
  const [selectedPlugin, setSelectedPlugin] = useState<string>('');
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [plugins, setPlugins] = useState<any[]>([]);

  useEffect(() => {
    api.get('/plugins').then(res => {
      setPlugins(res.data);
    });
  }, []);

  const executeAnalysis = async () => {
    setLoading(true);
    try {
      const response = await api.post(
        `/plugins/${selectedPlugin}/execute`,
        { params: parameters }
      );
      setResult(response.data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="plugin-analysis" style={{ display: 'flex', gap: 24 }}>
      {/* 左侧: 插件选择和参数配置 */}
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
          onClick={executeAnalysis}
          loading={loading}
          block
        >
          执行分析
        </Button>
      </Card>

      {/* 右侧: 结果展示 */}
      <Card title="分析结果" style={{ flex: 1 }}>
        <Spin spinning={loading}>
          {result && (
            <AnalysisResult
              plugin={selectedPlugin}
              data={result}
            />
          )}
        </Spin>
      </Card>
    </div>
  );
};

export default PluginAnalysis;
```

### 6.3 结果可视化组件

**DCF 估值结果**:
```typescript
// frontend/src/components/analysis/DCFResult.tsx
import React from 'react';
import { Card, Descriptions, Tag, Table } from 'antd';
import { LineChart, HeatMap } from '@ant-design/charts';

interface DCFData {
  enterprise_value: number;
  equity_value: number;
  per_share_value: number;
  current_price: number;
  upside_pct: number;
  sensitivity_table: Record<string, Record<string, number>>;
  cash_flows: Array<{ year: number; cf: number }>;
}

const DCFResult: React.FC<{ data: DCFData }> = ({ data }) => (
  <div className="dcf-result">
    <Card title="估值概览">
      <Descriptions column={2}>
        <Descriptions.Item label="企业价值">
          ¥{(data.enterprise_value / 1e8).toFixed(2)} 亿
        </Descriptions.Item>
        <Descriptions.Item label="股权价值">
          ¥{(data.equity_value / 1e8).toFixed(2)} 亿
        </Descriptions.Item>
        <Descriptions.Item label="每股价值">
          ¥{data.per_share_value.toFixed(2)}
        </Descriptions.Item>
        <Descriptions.Item label="当前价格">
          ¥{data.current_price.toFixed(2)}
        </Descriptions.Item>
        <Descriptions.Item label="上行空间">
          <Tag color={data.upside_pct > 0 ? 'green' : 'red'}>
            {data.upside_pct > 0 ? '+' : ''}{data.upside_pct.toFixed(1)}%
          </Tag>
        </Descriptions.Item>
      </Descriptions>
    </Card>

    <Card title="敏感性分析" style={{ marginTop: 16 }}>
      <HeatMap
        data={data.sensitivity_table}
        xField="wacc"
        yField="growth"
        colorField="value"
      />
    </Card>

    <Card title="现金流预测" style={{ marginTop: 16 }}>
      <LineChart
        data={data.cash_flows}
        xField="year"
        yField="cf"
      />
    </Card>
  </div>
);

export default DCFResult;
```

---

## 7. API 集成

### 7.1 插件 API 端点

```python
# src/web/api/plugins.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from src.plugins.registry import PluginRegistry
from src.web.deps import get_analysis_service

router = APIRouter(prefix="/plugins", tags=["plugins"])

class PluginExecuteRequest(BaseModel):
    symbol: str
    params: Dict[str, Any] = {}
    period: Optional[str] = None  # 可选期间参数

class AgentRunRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}

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
    request: PluginExecuteRequest,
    analysis_service = Depends(get_analysis_service)
):
    """执行插件分析"""
    plugin = PluginRegistry.get(plugin_name)
    if not plugin:
        raise HTTPException(404, f"Plugin {plugin_name} not found")

    result = await plugin.execute(
        stock_data=await analysis_service.get_stock(request.symbol),
        params=request.params
    )
    return result

@router.post("/agents/{agent_name}/run")
async def run_agent(
    agent_name: str,
    request: AgentRunRequest,
    analysis_service = Depends(get_analysis_service)
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

### 7.2 命令 API 端点

```python
# src/web/api/commands.py
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
    },
    {
        "name": "one-pager",
        "description": "公司简介",
        "plugin": "company_one_pager",
        "usage": "/one-pager <股票代码>"
    },
    {
        "name": "research",
        "description": "市场研究",
        "plugin": "market_researcher",
        "usage": "/research <行业>"
    }
]

@router.get("/")
async def list_commands() -> List[Dict]:
    """列出所有可用命令"""
    return COMMANDS
```

---

## 8. 实现路线图

### 阶段 1: 基础架构（1-2 天）

**任务**:
- [ ] 创建 `src/plugins/` 目录结构
- [ ] 实现插件基类 (`base.py`)
- [ ] 实现插件注册表 (`registry.py`)
- [ ] 实现连接器基类 (`src/data/connectors/base.py`)
- [ ] 实现连接器注册表 (`src/data/connectors/registry.py`)
- [ ] 添加插件 API 端点 (`src/web/api/plugins.py`)
- [ ] 添加命令 API 端点 (`src/web/api/commands.py`)

**产出**: 可运行的插件框架，支持插件注册和 API 调用

### 阶段 2: 核心插件（3-5 天）

**任务**:
- [ ] 实现 DCF 估值插件 (`src/plugins/financial_analysis/dcf.py`)
- [ ] 实现可比公司分析插件 (`src/plugins/financial_analysis/comps.py`)
- [ ] 实现股票筛选插件 (`src/plugins/financial_analysis/screening.py`)
- [ ] 实现财报分析插件 (`src/plugins/equity_research/earnings.py`)
- [ ] 实现公司简介插件 (`src/plugins/equity_research/one_pager.py`)
- [ ] 编写单元测试

**产出**: 5 个核心分析插件，可通过 API 调用

### 阶段 3: 代理工作流（2-3 天）

**任务**:
- [ ] 实现代理基类 (`src/plugins/agents/base.py`)
- [ ] 实现代理注册表 (`src/plugins/agents/registry.py`)
- [ ] 实现 Market Researcher 代理
- [ ] 实现 Earnings Reviewer 代理
- [ ] 集成到现有 Agent 模块
- [ ] 编写单元测试

**产出**: 2 个分析代理，支持对话式分析

### 阶段 4: 前端集成（2-3 天）

**任务**:
- [ ] 实现斜杠命令组件 (`frontend/src/components/SlashCommand.tsx`)
- [ ] 实现插件选择器 (`frontend/src/components/PluginSelector.tsx`)
- [ ] 实现参数表单 (`frontend/src/components/ParameterForm.tsx`)
- [ ] 实现插件分析页面 (`frontend/src/pages/PluginAnalysis.tsx`)
- [ ] 实现结果可视化组件 (`frontend/src/components/analysis/`)
- [ ] 集成到现有路由

**产出**: 完整的前端插件分析界面

### 阶段 5: 数据扩展（2-3 天）

**任务**:
- [ ] 实现港股数据连接器 (`src/data/connectors/hk_stock_connector.py`)
- [ ] 实现 Tushare 连接器 (`src/data/connectors/tushare_connector.py`)
- [ ] 扩展品种目录（港股）
- [ ] 测试端到端流程

**产出**: 支持港股数据，更多数据源可选

### 阶段 6: 测试与优化（1-2 天）

**任务**:
- [ ] 集成测试
- [ ] 性能优化
- [ ] 文档更新
- [ ] 代码审查

**产出**: 生产就绪的集成版本

---

## 9. 依赖关系

```
阶段 1 (基础架构)
    ↓
阶段 2 (核心插件) ← 阶段 3 (代理工作流)
    ↓
阶段 4 (前端集成)
    ↓
阶段 5 (数据扩展)
    ↓
阶段 6 (测试与优化)
```

---

## 10. 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 插件接口设计不合理 | 高 | 中 | 先实现 1-2 个插件验证接口，迭代改进 |
| AI 适配器兼容性问题 | 中 | 中 | 统一提示词格式，测试所有适配器 |
| 港股数据源不稳定 | 中 | 中 | 多数据源备份，实现降级策略 |
| 前端性能问题 | 低 | 低 | 懒加载插件，优化渲染 |
| 计算逻辑错误 | 高 | 中 | 单元测试覆盖，与参考实现对比验证 |

---

## 11. 成功标准

### 功能完整性
- [ ] 5 个核心分析插件可用
- [ ] 2 个分析代理可用
- [ ] 斜杠命令系统可用
- [ ] 港股数据可获取

### 性能指标
- [ ] 插件执行时间 < 30 秒
- [ ] 前端响应时间 < 3 秒
- [ ] 系统稳定性 > 99%

### 代码质量
- [ ] 单元测试覆盖率 > 80%
- [ ] 代码审查通过
- [ ] 文档完整

---

## 12. 后续扩展

### 短期扩展（1-3 个月）
- 更多分析插件（LBO 模型、并购分析）
- 更多代理（Portfolio Manager、Risk Manager）
- 更多数据源（Wind、Choice）

### 中期扩展（3-6 个月）
- 自定义插件系统
- 插件市场
- 机器学习模型集成

### 长期扩展（6-12 个月）
- 实时分析
- 自动化交易
- 风险管理系统

---

## 13. 参考资料

- [anthropics/financial-services](https://github.com/anthropics/financial-services)
- [stock-hub 项目文档](docs/)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [Ant Design 文档](https://ant.design/)
