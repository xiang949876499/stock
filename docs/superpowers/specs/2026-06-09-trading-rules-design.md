# Trading Rules 模块设计文档

> 将经典投资书籍整理成交易准则，集成到 AI 分析和回测验证

**版本**: 1.0.0
**日期**: 2026-06-09
**状态**: 设计完成

---

## 1. 项目概述

### 1.1 目标

将 7 本经典投资书籍的核心内容整理成结构化的交易准则，用于：
- **AI 分析参考**：AI 分析股票时自动参考相关准则
- **策略回测验证**：验证策略是否符合经典投资理念

### 1.2 书籍来源

| 序号 | 书名 | 作者 | 准则数量 |
|------|------|------|----------|
| 1 | 从零开始学炒股 | 未知 | 8 |
| 2 | 日本蜡烛图技术 | 史蒂夫·尼森 | 12 |
| 3 | 股票大作手回忆录 | 埃德温·勒菲弗 | 10 |
| 4 | 聪明的投资者 | 本杰明·格雷厄姆 | 10 |
| 5 | 交易心理分析 | 布里特·斯蒂恩博格 | 8 |
| 6 | 通向财务自由之路 | 范·K·撒普 | 8 |
| 7 | 投资最重要的事 | 霍华德·马克斯 | 8 |
| **总计** | | | **64** |

### 1.3 准则分类

| 类别 | 说明 | 数量 |
|------|------|------|
| selection | 选股阶段 | 12 |
| entry | 买入阶段 | 15 |
| holding | 持有阶段 | 8 |
| exit | 卖出阶段 | 12 |
| risk | 风控阶段 | 10 |
| **总计** | | **57** |

---

## 2. 准则结构设计

### 2.1 数据模型

```python
class TradingRule(BaseModel):
    """交易准则"""
    id: str                           # 唯一标识
    category: str                     # selection/entry/holding/exit/risk
    subcategory: str                  # 子类别
    source: str                       # 书籍来源
    author: str                       # 作者
    title: str                        # 标题
    summary: str                      # 精简版（1-2句）
    detail: str                       # 详细说明
    conditions: list[str]             # 适用条件
    warnings: list[str]               # 注意事项
    examples: list[str]               # 示例
    tags: list[str]                   # 标签
    weight: float                     # 权重（0-1）

class RuleCheckResult(BaseModel):
    """准则检查结果"""
    rule_id: str
    passed: bool
    score: float                      # 符合度（0-1）
    reason: str
```

### 2.2 准则示例

```json
{
    "id": "RULE_001",
    "category": "entry",
    "subcategory": "timing",
    "source": "日本蜡烛图技术",
    "author": "史蒂夫·尼森",
    "title": "底部反转形态买入",
    "summary": "出现锤子线、吞没形态等底部反转形态时，考虑买入",
    "detail": "当价格经过一段下跌后，出现以下形态时，表明可能见底：\n1. 锤子线：下影线长度至少是实体的2倍\n2. 看涨吞没：阳线完全包裹前一根阴线\n3. 早晨之星：三根K线组合，中间为十字星",
    "conditions": [
        "价格处于下跌趋势",
        "出现底部反转K线形态",
        "成交量配合放大"
    ],
    "warnings": [
        "需等待形态确认",
        "结合其他指标验证"
    ],
    "examples": ["600519 2024-01-15 锤子线反转"],
    "tags": ["技术分析", "K线", "买入时机"],
    "weight": 0.8
}
```

---

## 3. 模块架构

### 3.1 目录结构

```
src/trading_rules/
├── __init__.py
├── models.py               # 数据模型
├── rules.json              # 准则数据库
├── matcher.py              # 准则匹配器
├── checker.py              # 准则检查器
├── prompt_builder.py       # 提示词构建器
├── service.py              # 服务层
└── api.py                  # API 路由
```

### 3.2 核心组件

#### 3.2.1 准则匹配器（matcher.py）

```python
class RuleMatcher:
    """准则匹配器"""
    
    def match_by_scenario(self, scenario: str) -> list[TradingRule]:
        """按场景匹配准则"""
        # scenario: "买入" / "卖出" / "持有" / "止损"
        pass
    
    def match_by_tags(self, tags: list[str]) -> list[TradingRule]:
        """按标签匹配准则"""
        pass
    
    def match_by_stock(self, stock_data: dict) -> list[TradingRule]:
        """按股票特征匹配准则"""
        # 根据股票的技术指标、基本面等匹配相关准则
        pass
```

#### 3.2.2 准则检查器（checker.py）

```python
class RuleChecker:
    """准则检查器"""
    
    def check_entry_rules(self, stock_data: dict) -> list[RuleCheckResult]:
        """检查买入准则"""
        pass
    
    def check_exit_rules(self, stock_data: dict) -> list[RuleCheckResult]:
        """检查卖出准则"""
        pass
    
    def check_risk_rules(self, portfolio: dict) -> list[RuleCheckResult]:
        """检查风控准则"""
        pass
```

#### 3.2.3 提示词构建器（prompt_builder.py）

```python
class RulePromptBuilder:
    """提示词构建器"""
    
    def build_analysis_prompt(self, stock_data: dict, rules: list[TradingRule]) -> str:
        """构建带准则的分析提示词"""
        pass
    
    def build_check_prompt(self, stock_data: dict, check_results: list[RuleCheckResult]) -> str:
        """构建准则检查提示词"""
        pass
```

---

## 4. AI 分析集成

### 4.1 集成流程

```
1. 获取股票数据
2. 匹配相关准则（根据场景、标签、股票特征）
3. 构建带准则的提示词
4. AI 分析（参考准则）
5. 输出结果（包含准则检查）
```

### 4.2 提示词模板

```python
ANALYSIS_PROMPT_WITH_RULES = """
你是一个专业的股票分析师，请根据以下信息分析 {stock_name}({stock_code})。

## 股票数据
- 当前价格: {current_price}
- 技术指标: {technical_indicators}
- 基本面: {fundamentals}

## 交易准则（来自经典投资书籍）

### 买入准则
{entry_rules}

### 卖出准则
{exit_rules}

### 风控准则
{risk_rules}

## 分析要求
1. 基于股票数据进行分析
2. 参考交易准则给出建议
3. 指出符合/不符合哪些准则
4. 给出综合评分和建议

请以 JSON 格式输出：
{
    "score": 85,
    "signal": "buy",
    "trend": "bullish",
    "reason": "分析理由",
    "rules_check": {
        "passed": ["RULE_001", "RULE_003"],
        "failed": ["RULE_005"],
        "warnings": ["RULE_008"]
    }
}
"""
```

### 4.3 输出示例

```json
{
    "score": 75,
    "signal": "buy",
    "trend": "bullish",
    "reason": "技术面看多，基本面良好...",
    "rules_check": {
        "passed": [
            "RULE_001: 底部反转形态买入 ✓",
            "RULE_003: 趋势确认 ✓"
        ],
        "failed": [
            "RULE_005: 安全边际不足 ✗"
        ],
        "warnings": [
            "RULE_008: 需等待成交量确认"
        ]
    },
    "rules_summary": {
        "total": 10,
        "passed": 7,
        "failed": 2,
        "warnings": 1,
        "score": 0.7
    }
}
```

---

## 5. 回测验证集成

### 5.1 回测流程

```
1. 获取历史数据
2. 遍历每个交易日
3. 匹配当日适用的准则
4. 检查是否符合准则
5. 记录符合/不符合的交易
6. 统计准则有效性
```

### 5.2 准则有效性统计

```python
class RuleEffectiveness:
    """准则有效性统计"""
    
    rule_id: str
    total_trades: int          # 总交易次数
    passed_trades: int         # 符合准则的交易次数
    failed_trades: int         # 不符合准则的交易次数
    
    # 符合准则的交易表现
    passed_win_rate: float     # 胜率
    passed_avg_return: float   # 平均收益
    passed_max_drawdown: float # 最大回撤
    
    # 不符合准则的交易表现
    failed_win_rate: float
    failed_avg_return: float
    failed_max_drawdown: float
    
    # 准则贡献度
    contribution: float        # 准则对收益的贡献
```

### 5.3 回测报告示例

```json
{
    "backtest_id": "BT_20240101",
    "period": "2024-01-01 ~ 2024-12-31",
    "strategy": "comprehensive",
    
    "overall": {
        "total_trades": 100,
        "win_rate": 0.65,
        "avg_return": 0.08,
        "max_drawdown": 0.12,
        "sharpe_ratio": 1.5
    },
    
    "rules_effectiveness": [
        {
            "rule_id": "RULE_001",
            "title": "底部反转形态买入",
            "source": "日本蜡烛图技术",
            "total_trades": 20,
            "passed_win_rate": 0.75,
            "failed_win_rate": 0.45,
            "contribution": 0.15
        }
    ],
    
    "top_rules": [
        {"rule_id": "RULE_001", "contribution": 0.15},
        {"rule_id": "RULE_005", "contribution": 0.12},
        {"rule_id": "RULE_010", "contribution": 0.10}
    ]
}
```

---

## 6. API 接口

### 6.1 准则查询

```bash
# 获取所有准则
GET /api/v1/rules

# 获取单条准则
GET /api/v1/rules/{rule_id}

# 按类别获取准则
GET /api/v1/rules/category/{category}

# 搜索准则
GET /api/v1/rules/search?q={keyword}
```

### 6.2 准则检查

```bash
# 检查准则
POST /api/v1/rules/check
{
    "symbol": "600519",
    "market": "A",
    "scenario": "entry"
}

# 检查买入准则
POST /api/v1/rules/check/entry
{
    "symbol": "600519",
    "market": "A"
}

# 检查卖出准则
POST /api/v1/rules/check/exit
{
    "symbol": "600519",
    "market": "A"
}

# 检查风控准则
POST /api/v1/rules/check/risk
{
    "portfolio": {...}
}
```

### 6.3 准则统计

```bash
# 获取准则有效性统计
GET /api/v1/rules/effectiveness

# 获取单条准则统计
GET /api/v1/rules/effectiveness/{rule_id}
```

---

## 7. 书籍准则提取

### 7.1 从零开始学炒股

**核心准则**：
- 基础知识：股票基本概念、交易规则
- 技术分析基础：K线、均线、成交量
- 基本面分析：财报阅读、估值方法
- 交易心理：贪婪与恐惧

### 7.2 日本蜡烛图技术

**核心准则**：
- 单根K线形态：锤子线、上吊线、吞没形态
- 组合形态：早晨之星、黄昏之星、三只乌鸦
- 趋势确认：突破、回踩
- 关键点位：支撑位、阻力位

### 7.3 股票大作手回忆录

**核心准则**：
- 趋势跟踪：顺势而为
- 耐心等待：等待最佳时机
- 止损纪律：严格止损
- 仓位管理：分批建仓
- 市场记忆：历史会重演

### 7.4 聪明的投资者

**核心准则**：
- 安全边际：买入价格低于内在价值
- 长期持有：忽略短期波动
- 分散投资：不要把鸡蛋放在一个篮子里
- 价值投资：关注公司基本面
- 市场先生：市场是你的仆人，不是主人

### 7.5 交易心理分析

**核心准则**：
- 情绪管理：控制贪婪与恐惧
- 纪律执行：严格执行交易计划
- 认知偏差：避免锚定效应、确认偏差
- 心理账户：正确看待盈亏
- 自我认知：了解自己的风险承受能力

### 7.6 通向财务自由之路

**核心准则**：
- 系统化交易：建立交易系统
- 风险回报比：至少 1:2
- 期望值管理：正期望值系统
- 资金管理：凯利公式
- 持续改进：复盘与优化

### 7.7 投资最重要的事

**核心准则**：
- 第二层思维：超越市场共识
- 价值评估：准确评估内在价值
- 市场周期：理解周期规律
- 风险控制：风险优先于收益
- 逆向投资：在别人恐惧时贪婪

---

## 8. 实施计划

### 8.1 阶段 1：基础模块（1-2 天）

- 创建目录结构
- 实现数据模型
- 创建准则数据库（rules.json）
- 实现准则匹配器

### 8.2 阶段 2：检查器（1-2 天）

- 实现准则检查器
- 实现提示词构建器
- 集成到 AI 分析

### 8.3 阶段 3：API 接口（1 天）

- 实现准则查询 API
- 实现准则检查 API
- 实现准则统计 API

### 8.4 阶段 4：测试与文档（1 天）

- 编写单元测试
- 编写使用文档
- 集成测试

---

## 9. 总结

### 9.1 核心价值

- **知识沉淀**：将经典投资书籍的核心内容结构化
- **AI 增强**：让 AI 分析更专业、更有依据
- **策略验证**：用经典理念验证策略有效性

### 9.2 预期效果

- AI 分析准确率提升 10-20%
- 交易决策更有依据
- 减少情绪化交易

---

**文档完成时间**: 2026-06-09
**文档版本**: 1.0.0
**状态**: 设计完成，待用户审查
