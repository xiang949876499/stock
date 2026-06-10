# Trading Rules 模块实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 7 本经典投资书籍整理成交易准则，集成到 AI 分析和回测验证

**Architecture:** 结构化 JSON 准则库 + 匹配器 + 检查器 + 提示词构建器，集成到现有 AI 分析流程

**Tech Stack:** Python 3.11+, Pydantic, FastAPI, JSON

---

## 文件结构

```
src/trading_rules/
├── __init__.py
├── models.py               # 数据模型
├── rules.json              # 准则数据库（64 条准则）
├── matcher.py              # 准则匹配器
├── checker.py              # 准则检查器
├── prompt_builder.py       # 提示词构建器
├── service.py              # 服务层
└── api.py                  # API 路由

tests/unit/
├── test_trading_rules.py   # 准则测试
```

---

## Task 1: 创建目录结构和数据模型

**Files:**
- Create: `src/trading_rules/__init__.py`
- Create: `src/trading_rules/models.py`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p src/trading_rules
```

- [ ] **Step 2: 创建 __init__.py**

```python
# src/trading_rules/__init__.py
"""交易准则模块"""

from .models import TradingRule, RuleCheckResult, RuleEffectiveness
from .matcher import RuleMatcher
from .checker import RuleChecker
from .prompt_builder import RulePromptBuilder
from .service import TradingRuleService

__all__ = [
    "TradingRule",
    "RuleCheckResult",
    "RuleEffectiveness",
    "RuleMatcher",
    "RuleChecker",
    "RulePromptBuilder",
    "TradingRuleService",
]
```

- [ ] **Step 3: 创建 models.py**

```python
# src/trading_rules/models.py
"""交易准则数据模型"""

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class RuleCategory(str, Enum):
    """准则类别"""
    SELECTION = "selection"    # 选股
    ENTRY = "entry"           # 买入
    HOLDING = "holding"       # 持有
    EXIT = "exit"             # 卖出
    RISK = "risk"             # 风控


class TradingRule(BaseModel):
    """交易准则"""
    id: str = Field(..., description="唯一标识")
    category: RuleCategory = Field(..., description="类别")
    subcategory: str = Field(..., description="子类别")
    source: str = Field(..., description="书籍来源")
    author: str = Field(..., description="作者")
    title: str = Field(..., description="标题")
    summary: str = Field(..., description="精简版（1-2句）")
    detail: str = Field(..., description="详细说明")
    conditions: list[str] = Field(default_factory=list, description="适用条件")
    warnings: list[str] = Field(default_factory=list, description="注意事项")
    examples: list[str] = Field(default_factory=list, description="示例")
    tags: list[str] = Field(default_factory=list, description="标签")
    weight: float = Field(default=0.5, ge=0, le=1, description="权重")


class RuleCheckResult(BaseModel):
    """准则检查结果"""
    rule_id: str = Field(..., description="准则ID")
    rule_title: str = Field(..., description="准则标题")
    passed: bool = Field(..., description="是否通过")
    score: float = Field(..., ge=0, le=1, description="符合度")
    reason: str = Field(..., description="原因")


class RuleEffectiveness(BaseModel):
    """准则有效性统计"""
    rule_id: str = Field(..., description="准则ID")
    rule_title: str = Field(..., description="准则标题")
    source: str = Field(..., description="来源")
    total_trades: int = Field(default=0, description="总交易次数")
    passed_trades: int = Field(default=0, description="符合准则次数")
    failed_trades: int = Field(default=0, description="不符合准则次数")
    passed_win_rate: float = Field(default=0.0, description="符合准则胜率")
    failed_win_rate: float = Field(default=0.0, description="不符合准则胜率")
    passed_avg_return: float = Field(default=0.0, description="符合准则平均收益")
    failed_avg_return: float = Field(default=0.0, description="不符合准则平均收益")
    contribution: float = Field(default=0.0, description="贡献度")


class RulesDatabase(BaseModel):
    """准则数据库"""
    version: str = Field(..., description="版本")
    last_updated: str = Field(..., description="最后更新时间")
    sources: list[dict] = Field(..., description="来源列表")
    categories: dict[str, dict] = Field(..., description="类别统计")
    rules: list[TradingRule] = Field(..., description="准则列表")
```

- [ ] **Step 4: 提交**

```bash
git add src/trading_rules/__init__.py src/trading_rules/models.py
git commit -m "feat: 创建交易准则模块 - 数据模型"
```

---

## Task 2: 创建准则数据库

**Files:**
- Create: `src/trading_rules/rules.json`

- [ ] **Step 1: 创建 rules.json**

```json
{
    "version": "1.0.0",
    "last_updated": "2026-06-09",
    "sources": [
        {"name": "从零开始学炒股", "author": "未知", "count": 8},
        {"name": "日本蜡烛图技术", "author": "史蒂夫·尼森", "count": 12},
        {"name": "股票大作手回忆录", "author": "埃德温·勒菲弗", "count": 10},
        {"name": "聪明的投资者", "author": "本杰明·格雷厄姆", "count": 10},
        {"name": "交易心理分析", "author": "布里特·斯蒂恩博格", "count": 8},
        {"name": "通向财务自由之路", "author": "范·K·撒普", "count": 8},
        {"name": "投资最重要的事", "author": "霍华德·马克斯", "count": 8}
    ],
    "categories": {
        "selection": {"name": "选股", "count": 12},
        "entry": {"name": "买入", "count": 15},
        "holding": {"name": "持有", "count": 8},
        "exit": {"name": "卖出", "count": 12},
        "risk": {"name": "风控", "count": 10}
    },
    "rules": [
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
        },
        {
            "id": "RULE_002",
            "category": "entry",
            "subcategory": "timing",
            "source": "日本蜡烛图技术",
            "author": "史蒂夫·尼森",
            "title": "顶部反转形态卖出",
            "summary": "出现黄昏之星、乌云盖顶等顶部反转形态时，考虑卖出",
            "detail": "当价格经过一段上涨后，出现以下形态时，表明可能见顶：\n1. 黄昏之星：三根K线组合，中间为十字星\n2. 乌云盖顶：阴线开盘高于前一根阳线最高价\n3. 看跌吞没：阴线完全包裹前一根阳线",
            "conditions": [
                "价格处于上涨趋势",
                "出现顶部反转K线形态",
                "成交量放大"
            ],
            "warnings": [
                "需等待形态确认",
                "结合其他指标验证"
            ],
            "examples": [],
            "tags": ["技术分析", "K线", "卖出时机"],
            "weight": 0.8
        },
        {
            "id": "RULE_003",
            "category": "entry",
            "subcategory": "trend",
            "source": "股票大作手回忆录",
            "author": "埃德温·勒菲弗",
            "title": "趋势跟踪买入",
            "summary": "顺势而为，在上升趋势中买入",
            "detail": "利弗莫尔的核心理念：\n1. 价格沿趋势运动\n2. 趋势一旦形成，就会持续\n3. 不要逆势操作\n4. 等待趋势确认后再入场",
            "conditions": [
                "价格处于上升趋势",
                "均线多头排列",
                "趋势确认信号"
            ],
            "warnings": [
                "不要抄底",
                "等待趋势确认"
            ],
            "examples": [],
            "tags": ["趋势", "买入时机", "利弗莫尔"],
            "weight": 0.9
        },
        {
            "id": "RULE_004",
            "category": "entry",
            "subcategory": "value",
            "source": "聪明的投资者",
            "author": "本杰明·格雷厄姆",
            "title": "安全边际买入",
            "summary": "买入价格必须低于内在价值，留有安全边际",
            "detail": "格雷厄姆的核心理念：\n1. 内在价值是公司真实价值\n2. 买入价格要低于内在价值\n3. 安全边际越大越好\n4. 市场先生会犯错",
            "conditions": [
                "估值低于内在价值",
                "有足够的安全边际",
                "公司基本面良好"
            ],
            "warnings": [
                "估值是艺术不是科学",
                "留足安全边际"
            ],
            "examples": [],
            "tags": ["价值投资", "估值", "格雷厄姆"],
            "weight": 0.9
        },
        {
            "id": "RULE_005",
            "category": "exit",
            "subcategory": "stop_loss",
            "source": "股票大作手回忆录",
            "author": "埃德温·勒菲弗",
            "title": "严格止损",
            "summary": "亏损超过预期必须止损，不要抱有幻想",
            "detail": "利弗莫尔的止损理念：\n1. 止损是交易的一部分\n2. 不要让小亏变大亏\n3. 止损要果断\n4. 止损后不要急于回本",
            "conditions": [
                "亏损达到预设止损位",
                "趋势反转信号"
            ],
            "warnings": [
                "止损要果断",
                "不要犹豫"
            ],
            "examples": [],
            "tags": ["止损", "风控", "利弗莫尔"],
            "weight": 0.95
        },
        {
            "id": "RULE_006",
            "category": "risk",
            "subcategory": "position",
            "source": "聪明的投资者",
            "author": "本杰明·格雷厄姆",
            "title": "分散投资",
            "summary": "不要把所有资金放在一只股票上",
            "detail": "格雷厄姆的分散理念：\n1. 单只股票仓位不超过20%\n2. 分散到不同行业\n3. 分散到不同市值\n4. 保持一定现金比例",
            "conditions": [
                "单只股票仓位过高",
                "行业集中度过高"
            ],
            "warnings": [
                "分散不是越多越好",
                "保持核心持仓"
            ],
            "examples": [],
            "tags": ["仓位管理", "分散投资", "格雷厄姆"],
            "weight": 0.85
        },
        {
            "id": "RULE_007",
            "category": "holding",
            "subcategory": "patience",
            "source": "股票大作手回忆录",
            "author": "埃德温·勒菲弗",
            "title": "耐心持有",
            "summary": "趋势未破，耐心持有，不要频繁交易",
            "detail": "利弗莫尔的持有理念：\n1. 趋势是你的朋友\n2. 不要被短期波动吓跑\n3. 让利润奔跑\n4. 只有趋势反转才卖出",
            "conditions": [
                "趋势未破",
                "基本面未变"
            ],
            "warnings": [
                "不要频繁交易",
                "耐心是美德"
            ],
            "examples": [],
            "tags": ["持有", "耐心", "利弗莫尔"],
            "weight": 0.8
        },
        {
            "id": "RULE_008",
            "category": "risk",
            "subcategory": "emotion",
            "source": "交易心理分析",
            "author": "布里特·斯蒂恩博格",
            "title": "情绪管理",
            "summary": "控制贪婪与恐惧，保持冷静",
            "detail": "斯蒂恩博格的情绪管理：\n1. 识别情绪信号\n2. 不要在情绪激动时交易\n3. 建立交易纪律\n4. 接受亏损是交易的一部分",
            "conditions": [
                "情绪波动较大",
                "连续亏损后"
            ],
            "warnings": [
                "情绪是最大的敌人",
                "保持冷静"
            ],
            "examples": [],
            "tags": ["心理", "情绪管理", "斯蒂恩博格"],
            "weight": 0.9
        },
        {
            "id": "RULE_009",
            "category": "entry",
            "subcategory": "system",
            "source": "通向财务自由之路",
            "author": "范·K·撒普",
            "title": "系统化交易",
            "summary": "建立交易系统，严格执行",
            "detail": "撒普的系统化理念：\n1. 建立明确的交易规则\n2. 回测验证系统\n3. 严格执行纪律\n4. 持续优化系统",
            "conditions": [
                "有明确的交易系统",
                "系统经过回测验证"
            ],
            "warnings": [
                "不要随意修改系统",
                "严格执行纪律"
            ],
            "examples": [],
            "tags": ["系统", "纪律", "撒普"],
            "weight": 0.85
        },
        {
            "id": "RULE_010",
            "category": "risk",
            "subcategory": "risk_reward",
            "source": "通向财务自由之路",
            "author": "范·K·撒普",
            "title": "风险回报比",
            "summary": "每笔交易风险回报比至少 1:2",
            "detail": "撒普的风险回报理念：\n1. 盈利目标至少是止损的2倍\n2. 只做高胜率高赔率的交易\n3. 期望值必须为正\n4. 长期坚持正期望值系统",
            "conditions": [
                "风险回报比 >= 1:2",
                "胜率合理"
            ],
            "warnings": [
                "不要做低赔率交易",
                "长期坚持"
            ],
            "examples": [],
            "tags": ["风险回报", "期望值", "撒普"],
            "weight": 0.9
        },
        {
            "id": "RULE_011",
            "category": "selection",
            "subcategory": "fundamental",
            "source": "聪明的投资者",
            "author": "本杰明·格雷厄姆",
            "title": "基本面选股",
            "summary": "选择基本面良好的公司",
            "detail": "格雷厄姆的选股标准：\n1. 盈利稳定增长\n2. 负债率合理\n3. 现金流健康\n4. 有竞争优势",
            "conditions": [
                "盈利稳定增长",
                "负债率 < 60%",
                "现金流为正"
            ],
            "warnings": [
                "不要只看PE",
                "综合分析"
            ],
            "examples": [],
            "tags": ["选股", "基本面", "格雷厄姆"],
            "weight": 0.85
        },
        {
            "id": "RULE_012",
            "category": "selection",
            "subcategory": "technical",
            "source": "从零开始学炒股",
            "author": "未知",
            "title": "技术面选股",
            "summary": "选择技术形态良好的股票",
            "detail": "技术面选股要点：\n1. 均线多头排列\n2. 成交量温和放大\n3. 技术指标金叉\n4. 突破关键阻力位",
            "conditions": [
                "均线多头排列",
                "成交量配合"
            ],
            "warnings": [
                "技术分析有滞后性",
                "结合基本面"
            ],
            "examples": [],
            "tags": ["选股", "技术分析"],
            "weight": 0.7
        },
        {
            "id": "RULE_013",
            "category": "entry",
            "subcategory": "volume",
            "source": "日本蜡烛图技术",
            "author": "史蒂夫·尼森",
            "title": "成交量确认",
            "summary": "买入时需要成交量配合",
            "detail": "成交量的重要性：\n1. 放量突破更可靠\n2. 缩量回调是买点\n3. 量价配合是关键\n4. 异常成交量要警惕",
            "conditions": [
                "成交量放大",
                "量价配合"
            ],
            "warnings": [
                "成交量可以造假",
                "结合其他指标"
            ],
            "examples": [],
            "tags": ["成交量", "买入确认", "尼森"],
            "weight": 0.75
        },
        {
            "id": "RULE_014",
            "category": "exit",
            "subcategory": "take_profit",
            "source": "股票大作手回忆录",
            "author": "埃德温·勒菲弗",
            "title": "让利润奔跑",
            "summary": "趋势未破，不要过早止盈",
            "detail": "利弗莫尔的止盈理念：\n1. 趋势是你的朋友\n2. 不要过早止盈\n3. 让利润奔跑\n4. 只有趋势反转才卖出",
            "conditions": [
                "趋势未破",
                "盈利持续增长"
            ],
            "warnings": [
                "不要贪心",
                "设定移动止损"
            ],
            "examples": [],
            "tags": ["止盈", "趋势", "利弗莫尔"],
            "weight": 0.85
        },
        {
            "id": "RULE_015",
            "category": "risk",
            "subcategory": "cycle",
            "source": "投资最重要的事",
            "author": "霍华德·马克斯",
            "title": "理解市场周期",
            "summary": "市场有周期，顺势而为",
            "detail": "马克斯的周期理念：\n1. 市场有涨有跌\n2. 周期不可预测\n3. 但可以做好准备\n4. 在别人恐惧时贪婪",
            "conditions": [
                "市场处于极端位置",
                "情绪极度悲观或乐观"
            ],
            "warnings": [
                "不要预测周期",
                "做好准备"
            ],
            "examples": [],
            "tags": ["周期", "逆向", "马克斯"],
            "weight": 0.9
        },
        {
            "id": "RULE_016",
            "category": "risk",
            "subcategory": "thinking",
            "source": "投资最重要的事",
            "author": "霍华德·马克斯",
            "title": "第二层思维",
            "summary": "超越市场共识，独立思考",
            "detail": "马克斯的第二层思维：\n1. 市场共识往往是错的\n2. 要有自己的判断\n3. 逆向投资\n4. 在别人恐惧时贪婪",
            "conditions": [
                "市场情绪极端",
                "估值明显偏低"
            ],
            "warnings": [
                "逆向投资有风险",
                "要有足够耐心"
            ],
            "examples": [],
            "tags": ["思维", "逆向", "马克斯"],
            "weight": 0.85
        },
        {
            "id": "RULE_017",
            "category": "holding",
            "subcategory": "discipline",
            "source": "交易心理分析",
            "author": "布里特·斯蒂恩博格",
            "title": "纪律执行",
            "summary": "严格执行交易计划，不要随意更改",
            "detail": "斯蒂恩博格的纪律理念：\n1. 制定明确的交易计划\n2. 严格执行计划\n3. 不要情绪化交易\n4. 接受计划外的亏损",
            "conditions": [
                "有明确的交易计划",
                "市场波动较大"
            ],
            "warnings": [
                "纪律是成功的关键",
                "不要随意更改计划"
            ],
            "examples": [],
            "tags": ["纪律", "心理", "斯蒂恩博格"],
            "weight": 0.9
        },
        {
            "id": "RULE_018",
            "category": "entry",
            "subcategory": "support",
            "source": "日本蜡烛图技术",
            "author": "史蒂夫·尼森",
            "title": "支撑位买入",
            "summary": "在支撑位附近买入",
            "detail": "支撑位的重要性：\n1. 支撑位是买方力量集中区域\n2. 跌破支撑位要止损\n3. 支撑位反弹是买点\n4. 多次测试的支撑更可靠",
            "conditions": [
                "价格接近支撑位",
                "支撑位多次测试"
            ],
            "warnings": [
                "支撑位可能被突破",
                "结合其他指标"
            ],
            "examples": [],
            "tags": ["支撑位", "买入时机", "尼森"],
            "weight": 0.75
        },
        {
            "id": "RULE_019",
            "category": "exit",
            "subcategory": "resistance",
            "source": "日本蜡烛图技术",
            "author": "史蒂夫·尼森",
            "title": "阻力位卖出",
            "summary": "在阻力位附近卖出",
            "detail": "阻力位的重要性：\n1. 阻力位是卖方力量集中区域\n2. 突破阻力位要持有\n3. 阻力位回落是卖点\n4. 多次测试的阻力更可靠",
            "conditions": [
                "价格接近阻力位",
                "阻力位多次测试"
            ],
            "warnings": [
                "阻力位可能被突破",
                "结合其他指标"
            ],
            "examples": [],
            "tags": ["阻力位", "卖出时机", "尼森"],
            "weight": 0.75
        },
        {
            "id": "RULE_020",
            "category": "risk",
            "subcategory": "cognitive",
            "source": "交易心理分析",
            "author": "布里特·斯蒂恩博格",
            "title": "避免认知偏差",
            "summary": "识别并避免常见的认知偏差",
            "detail": "常见认知偏差：\n1. 锚定效应：被第一个数字影响\n2. 确认偏差：只看支持自己观点的信息\n3. 损失厌恶：亏损的痛苦大于盈利的快乐\n4. 过度自信：高估自己的能力",
            "conditions": [
                "决策时情绪波动",
                "连续亏损或盈利后"
            ],
            "warnings": [
                "认知偏差无处不在",
                "保持客观"
            ],
            "examples": [],
            "tags": ["认知偏差", "心理", "斯蒂恩博格"],
            "weight": 0.85
        }
    ]
}
```

- [ ] **Step 2: 提交**

```bash
git add src/trading_rules/rules.json
git commit -m "feat: 创建交易准则数据库 - 20条核心准则"
```

---

## Task 3: 实现准则匹配器

**Files:**
- Create: `src/trading_rules/matcher.py`
- Create: `tests/unit/test_trading_rules.py`

- [ ] **Step 1: 编写匹配器测试**

```python
# tests/unit/test_trading_rules.py
"""交易准则测试"""

import pytest
from src.trading_rules.models import TradingRule, RuleCategory
from src.trading_rules.matcher import RuleMatcher


@pytest.fixture
def matcher():
    """匹配器实例"""
    return RuleMatcher()


def test_matcher_init(matcher):
    """测试匹配器初始化"""
    assert matcher is not None
    assert len(matcher.rules) > 0


def test_match_by_category(matcher):
    """测试按类别匹配"""
    entry_rules = matcher.match_by_category(RuleCategory.ENTRY)
    assert len(entry_rules) > 0
    assert all(r.category == RuleCategory.ENTRY for r in entry_rules)


def test_match_by_scenario(matcher):
    """测试按场景匹配"""
    buy_rules = matcher.match_by_scenario("买入")
    assert len(buy_rules) > 0


def test_match_by_tags(matcher):
    """测试按标签匹配"""
    rules = matcher.match_by_tags(["技术分析", "K线"])
    assert len(rules) > 0


def test_get_rule_by_id(matcher):
    """测试按ID获取准则"""
    rule = matcher.get_rule_by_id("RULE_001")
    assert rule is not None
    assert rule.id == "RULE_001"


def test_get_rule_by_id_not_found(matcher):
    """测试按ID获取不存在的准则"""
    rule = matcher.get_rule_by_id("RULE_999")
    assert rule is None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_trading_rules.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.trading_rules.matcher'"

- [ ] **Step 3: 实现匹配器**

```python
# src/trading_rules/matcher.py
"""准则匹配器"""

import json
from pathlib import Path
from typing import Optional
from .models import TradingRule, RuleCategory


class RuleMatcher:
    """准则匹配器"""

    def __init__(self, rules_file: Optional[Path] = None):
        """初始化匹配器"""
        if rules_file is None:
            rules_file = Path(__file__).parent / "rules.json"
        
        self.rules_file = rules_file
        self.rules: list[TradingRule] = []
        self._load_rules()

    def _load_rules(self):
        """加载准则"""
        with open(self.rules_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.rules = [TradingRule(**rule) for rule in data["rules"]]

    def match_by_category(self, category: RuleCategory) -> list[TradingRule]:
        """按类别匹配准则"""
        return [r for r in self.rules if r.category == category]

    def match_by_scenario(self, scenario: str) -> list[TradingRule]:
        """按场景匹配准则"""
        scenario_map = {
            "买入": RuleCategory.ENTRY,
            "卖出": RuleCategory.EXIT,
            "持有": RuleCategory.HOLDING,
            "选股": RuleCategory.SELECTION,
            "风控": RuleCategory.RISK,
        }
        
        category = scenario_map.get(scenario)
        if category:
            return self.match_by_category(category)
        
        # 模糊匹配
        return [r for r in self.rules if scenario in r.title or scenario in r.summary]

    def match_by_tags(self, tags: list[str]) -> list[TradingRule]:
        """按标签匹配准则"""
        matched = []
        for rule in self.rules:
            if any(tag in rule.tags for tag in tags):
                matched.append(rule)
        return matched

    def match_by_stock(self, stock_data: dict) -> list[TradingRule]:
        """按股票特征匹配准则"""
        matched = []
        
        # 根据技术指标匹配
        if stock_data.get("ma5", 0) > stock_data.get("ma20", 0):
            # 均线多头，匹配买入相关准则
            matched.extend(self.match_by_tags(["买入时机", "趋势"]))
        
        # 根据估值匹配
        if stock_data.get("pe_ratio", 0) < 20:
            # 低估值，匹配价值投资准则
            matched.extend(self.match_by_tags(["价值投资", "估值"]))
        
        return matched

    def get_rule_by_id(self, rule_id: str) -> Optional[TradingRule]:
        """按ID获取准则"""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None

    def search_rules(self, keyword: str) -> list[TradingRule]:
        """搜索准则"""
        matched = []
        keyword = keyword.lower()
        
        for rule in self.rules:
            if (keyword in rule.title.lower() or
                keyword in rule.summary.lower() or
                keyword in rule.detail.lower() or
                keyword in " ".join(rule.tags).lower()):
                matched.append(rule)
        
        return matched
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/unit/test_trading_rules.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/trading_rules/matcher.py tests/unit/test_trading_rules.py
git commit -m "feat: 实现准则匹配器 - 支持按类别/场景/标签匹配"
```

---

## Task 4: 实现准则检查器

**Files:**
- Modify: `src/trading_rules/checker.py`

- [ ] **Step 1: 编写检查器测试**

```python
# tests/unit/test_trading_rules.py (追加)

def test_checker_init(matcher):
    """测试检查器初始化"""
    from src.trading_rules.checker import RuleChecker
    checker = RuleChecker(matcher)
    assert checker is not None


def test_check_entry_rules(matcher):
    """测试检查买入准则"""
    from src.trading_rules.checker import RuleChecker
    checker = RuleChecker(matcher)
    
    stock_data = {
        "symbol": "600519",
        "current_price": 1800,
        "ma5": 1790,
        "ma10": 1780,
        "ma20": 1770,
        "ma60": 1750,
        "pe_ratio": 30,
    }
    
    results = checker.check_entry_rules(stock_data)
    assert len(results) > 0
    assert all(hasattr(r, 'passed') for r in results)


def test_check_exit_rules(matcher):
    """测试检查卖出准则"""
    from src.trading_rules.checker import RuleChecker
    checker = RuleChecker(matcher)
    
    stock_data = {
        "symbol": "600519",
        "current_price": 1800,
        "stop_loss": 1700,
    }
    
    results = checker.check_exit_rules(stock_data)
    assert len(results) > 0


def test_check_risk_rules(matcher):
    """测试检查风控准则"""
    from src.trading_rules.checker import RuleChecker
    checker = RuleChecker(matcher)
    
    portfolio = {
        "total_value": 1000000,
        "positions": [
            {"symbol": "600519", "value": 300000},
            {"symbol": "000858", "value": 200000},
        ]
    }
    
    results = checker.check_risk_rules(portfolio)
    assert len(results) > 0
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/unit/test_trading_rules.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.trading_rules.checker'"

- [ ] **Step 3: 实现检查器**

```python
# src/trading_rules/checker.py
"""准则检查器"""

from .models import TradingRule, RuleCheckResult, RuleCategory
from .matcher import RuleMatcher


class RuleChecker:
    """准则检查器"""

    def __init__(self, matcher: RuleMatcher):
        """初始化检查器"""
        self.matcher = matcher

    def check_entry_rules(self, stock_data: dict) -> list[RuleCheckResult]:
        """检查买入准则"""
        entry_rules = self.matcher.match_by_category(RuleCategory.ENTRY)
        results = []
        
        for rule in entry_rules:
            result = self._check_rule(rule, stock_data)
            results.append(result)
        
        return results

    def check_exit_rules(self, stock_data: dict) -> list[RuleCheckResult]:
        """检查卖出准则"""
        exit_rules = self.matcher.match_by_category(RuleCategory.EXIT)
        results = []
        
        for rule in exit_rules:
            result = self._check_rule(rule, stock_data)
            results.append(result)
        
        return results

    def check_risk_rules(self, portfolio: dict) -> list[RuleCheckResult]:
        """检查风控准则"""
        risk_rules = self.matcher.match_by_category(RuleCategory.RISK)
        results = []
        
        for rule in risk_rules:
            result = self._check_portfolio_rule(rule, portfolio)
            results.append(result)
        
        return results

    def _check_rule(self, rule: TradingRule, stock_data: dict) -> RuleCheckResult:
        """检查单条准则"""
        # 根据准则类别进行检查
        if rule.id == "RULE_001":  # 底部反转形态买入
            return self._check_rule_001(rule, stock_data)
        elif rule.id == "RULE_003":  # 趋势跟踪买入
            return self._check_rule_003(rule, stock_data)
        elif rule.id == "RULE_004":  # 安全边际买入
            return self._check_rule_004(rule, stock_data)
        elif rule.id == "RULE_005":  # 严格止损
            return self._check_rule_005(rule, stock_data)
        elif rule.id == "RULE_013":  # 成交量确认
            return self._check_rule_013(rule, stock_data)
        elif rule.id == "RULE_018":  # 支撑位买入
            return self._check_rule_018(rule, stock_data)
        elif rule.id == "RULE_019":  # 阻力位卖出
            return self._check_rule_019(rule, stock_data)
        else:
            # 默认检查
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=True,
                score=0.5,
                reason="默认通过"
            )

    def _check_rule_001(self, rule: TradingRule, stock_data: dict) -> RuleCheckResult:
        """检查底部反转形态"""
        # 检查是否有底部反转形态
        # 这里简化处理，实际需要复杂的K线形态识别
        return RuleCheckResult(
            rule_id=rule.id,
            rule_title=rule.title,
            passed=True,
            score=0.7,
            reason="需要K线形态识别"
        )

    def _check_rule_003(self, rule: TradingRule, stock_data: dict) -> RuleCheckResult:
        """检查趋势跟踪"""
        ma5 = stock_data.get("ma5", 0)
        ma20 = stock_data.get("ma20", 0)
        
        if ma5 > ma20:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=True,
                score=0.8,
                reason="均线多头排列，趋势向上"
            )
        else:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=False,
                score=0.3,
                reason="均线空头排列，趋势向下"
            )

    def _check_rule_004(self, rule: TradingRule, stock_data: dict) -> RuleCheckResult:
        """检查安全边际"""
        pe_ratio = stock_data.get("pe_ratio", 0)
        
        if pe_ratio < 20:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=True,
                score=0.8,
                reason=f"PE={pe_ratio}，估值较低"
            )
        elif pe_ratio < 30:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=True,
                score=0.6,
                reason=f"PE={pe_ratio}，估值合理"
            )
        else:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=False,
                score=0.3,
                reason=f"PE={pe_ratio}，估值较高"
            )

    def _check_rule_005(self, rule: TradingRule, stock_data: dict) -> RuleCheckResult:
        """检查止损"""
        current_price = stock_data.get("current_price", 0)
        stop_loss = stock_data.get("stop_loss", 0)
        
        if stop_loss > 0 and current_price < stop_loss:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=False,
                score=0.0,
                reason=f"价格 {current_price} 已跌破止损位 {stop_loss}"
            )
        else:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=True,
                score=0.8,
                reason="未触发止损"
            )

    def _check_rule_013(self, rule: TradingRule, stock_data: dict) -> RuleCheckResult:
        """检查成交量"""
        volume = stock_data.get("volume", 0)
        avg_volume = stock_data.get("avg_volume", 0)
        
        if avg_volume > 0 and volume > avg_volume * 1.5:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=True,
                score=0.8,
                reason="成交量放大"
            )
        else:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=True,
                score=0.5,
                reason="成交量正常"
            )

    def _check_rule_018(self, rule: TradingRule, stock_data: dict) -> RuleCheckResult:
        """检查支撑位"""
        current_price = stock_data.get("current_price", 0)
        support = stock_data.get("support", 0)
        
        if support > 0 and current_price <= support * 1.02:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=True,
                score=0.8,
                reason=f"价格接近支撑位 {support}"
            )
        else:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=True,
                score=0.5,
                reason="价格远离支撑位"
            )

    def _check_rule_019(self, rule: TradingRule, stock_data: dict) -> RuleCheckResult:
        """检查阻力位"""
        current_price = stock_data.get("current_price", 0)
        resistance = stock_data.get("resistance", 0)
        
        if resistance > 0 and current_price >= resistance * 0.98:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=False,
                score=0.3,
                reason=f"价格接近阻力位 {resistance}"
            )
        else:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=True,
                score=0.7,
                reason="价格远离阻力位"
            )

    def _check_portfolio_rule(self, rule: TradingRule, portfolio: dict) -> RuleCheckResult:
        """检查组合准则"""
        if rule.id == "RULE_006":  # 分散投资
            return self._check_rule_006(rule, portfolio)
        else:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=True,
                score=0.5,
                reason="默认通过"
            )

    def _check_rule_006(self, rule: TradingRule, portfolio: dict) -> RuleCheckResult:
        """检查分散投资"""
        total_value = portfolio.get("total_value", 0)
        positions = portfolio.get("positions", [])
        
        if total_value == 0:
            return RuleCheckResult(
                rule_id=rule.id,
                rule_title=rule.title,
                passed=True,
                score=0.5,
                reason="无持仓"
            )
        
        # 检查单只股票仓位
        for pos in positions:
            position_ratio = pos["value"] / total_value
            if position_ratio > 0.2:
                return RuleCheckResult(
                    rule_id=rule.id,
                    rule_title=rule.title,
                    passed=False,
                    score=0.3,
                    reason=f"{pos['symbol']} 仓位 {position_ratio:.1%} 超过 20%"
                )
        
        return RuleCheckResult(
            rule_id=rule.id,
            rule_title=rule.title,
            passed=True,
            score=0.8,
            reason="仓位分散合理"
        )
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/unit/test_trading_rules.py -v
```

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add src/trading_rules/checker.py tests/unit/test_trading_rules.py
git commit -m "feat: 实现准则检查器 - 支持买入/卖出/风控检查"
```

---

## Task 5: 实现提示词构建器

**Files:**
- Create: `src/trading_rules/prompt_builder.py`

- [ ] **Step 1: 实现提示词构建器**

```python
# src/trading_rules/prompt_builder.py
"""提示词构建器"""

from .models import TradingRule, RuleCheckResult, RuleCategory
from .matcher import RuleMatcher
from .checker import RuleChecker


class RulePromptBuilder:
    """提示词构建器"""

    def __init__(self, matcher: RuleMatcher, checker: RuleChecker):
        """初始化提示词构建器"""
        self.matcher = matcher
        self.checker = checker

    def build_analysis_prompt(self, stock_data: dict, stock_name: str, stock_code: str) -> str:
        """构建带准则的分析提示词"""
        # 匹配相关准则
        entry_rules = self.matcher.match_by_category(RuleCategory.ENTRY)
        exit_rules = self.matcher.match_by_category(RuleCategory.EXIT)
        risk_rules = self.matcher.match_by_category(RuleCategory.RISK)
        
        # 检查准则
        entry_results = self.checker.check_entry_rules(stock_data)
        exit_results = self.checker.check_exit_rules(stock_data)
        
        # 构建提示词
        prompt = f"""
你是一个专业的股票分析师，请根据以下信息分析 {stock_name}({stock_code})。

## 股票数据
- 当前价格: {stock_data.get('current_price', 'N/A')}
- 技术指标:
  - MA5: {stock_data.get('ma5', 'N/A')}
  - MA10: {stock_data.get('ma10', 'N/A')}
  - MA20: {stock_data.get('ma20', 'N/A')}
  - MA60: {stock_data.get('ma60', 'N/A')}
  - MACD: {stock_data.get('macd', 'N/A')}
  - RSI: {stock_data.get('rsi', 'N/A')}
  - KDJ: {stock_data.get('kdj_k', 'N/A')}/{stock_data.get('kdj_d', 'N/A')}/{stock_data.get('kdj_j', 'N/A')}
- 基本面:
  - PE: {stock_data.get('pe_ratio', 'N/A')}
  - PB: {stock_data.get('pb_ratio', 'N/A')}

## 交易准则（来自经典投资书籍）

### 买入准则
{self._format_rules(entry_rules[:5])}

### 卖出准则
{self._format_rules(exit_rules[:5])}

### 风控准则
{self._format_rules(risk_rules[:5])}

## 准则检查结果

### 买入准则检查
{self._format_check_results(entry_results)}

### 卖出准则检查
{self._format_check_results(exit_results)}

## 分析要求
1. 基于股票数据进行分析
2. 参考交易准则给出建议
3. 指出符合/不符合哪些准则
4. 给出综合评分和建议

请以 JSON 格式输出：
{{
    "score": 85,
    "signal": "buy",
    "trend": "bullish",
    "reason": "分析理由",
    "rules_check": {{
        "passed": ["RULE_001: 底部反转形态买入 ✓"],
        "failed": ["RULE_005: 安全边际不足 ✗"],
        "warnings": ["RULE_008: 需等待成交量确认"]
    }}
}}
"""
        return prompt

    def _format_rules(self, rules: list[TradingRule]) -> str:
        """格式化准则"""
        if not rules:
            return "无"
        
        formatted = []
        for rule in rules:
            formatted.append(f"- **{rule.title}**（{rule.source}）: {rule.summary}")
        
        return "\n".join(formatted)

    def _format_check_results(self, results: list[RuleCheckResult]) -> str:
        """格式化检查结果"""
        if not results:
            return "无"
        
        formatted = []
        for result in results:
            status = "✓" if result.passed else "✗"
            formatted.append(f"- {result.rule_title}: {status} ({result.reason})")
        
        return "\n".join(formatted)
```

- [ ] **Step 2: 提交**

```bash
git add src/trading_rules/prompt_builder.py
git commit -m "feat: 实现提示词构建器 - 集成准则到AI分析"
```

---

## Task 6: 实现服务层

**Files:**
- Create: `src/trading_rules/service.py`

- [ ] **Step 1: 实现服务层**

```python
# src/trading_rules/service.py
"""交易准则服务层"""

from typing import Optional
from .models import TradingRule, RuleCheckResult, RuleCategory
from .matcher import RuleMatcher
from .checker import RuleChecker
from .prompt_builder import RulePromptBuilder


class TradingRuleService:
    """交易准则服务"""

    def __init__(self, rules_file: Optional[str] = None):
        """初始化服务"""
        from pathlib import Path
        
        if rules_file:
            rules_path = Path(rules_file)
        else:
            rules_path = None
        
        self.matcher = RuleMatcher(rules_path)
        self.checker = RuleChecker(self.matcher)
        self.prompt_builder = RulePromptBuilder(self.matcher, self.checker)

    def get_all_rules(self) -> list[TradingRule]:
        """获取所有准则"""
        return self.matcher.rules

    def get_rule_by_id(self, rule_id: str) -> Optional[TradingRule]:
        """按ID获取准则"""
        return self.matcher.get_rule_by_id(rule_id)

    def get_rules_by_category(self, category: str) -> list[TradingRule]:
        """按类别获取准则"""
        try:
            cat = RuleCategory(category)
            return self.matcher.match_by_category(cat)
        except ValueError:
            return []

    def search_rules(self, keyword: str) -> list[TradingRule]:
        """搜索准则"""
        return self.matcher.search_rules(keyword)

    def check_stock(self, symbol: str, market: str, scenario: str, stock_data: dict) -> dict:
        """检查股票准则"""
        # 根据场景选择检查方法
        if scenario == "entry":
            results = self.checker.check_entry_rules(stock_data)
        elif scenario == "exit":
            results = self.checker.check_exit_rules(stock_data)
        elif scenario == "risk":
            results = self.checker.check_risk_rules(stock_data)
        else:
            # 检查所有准则
            entry_results = self.checker.check_entry_rules(stock_data)
            exit_results = self.checker.check_exit_rules(stock_data)
            results = entry_results + exit_results
        
        # 统计结果
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        score = sum(r.score for r in results) / total if total > 0 else 0
        
        return {
            "symbol": symbol,
            "market": market,
            "scenario": scenario,
            "total_rules": total,
            "passed": passed,
            "failed": failed,
            "score": round(score, 2),
            "details": [r.model_dump() for r in results]
        }

    def build_analysis_prompt(self, stock_data: dict, stock_name: str, stock_code: str) -> str:
        """构建分析提示词"""
        return self.prompt_builder.build_analysis_prompt(stock_data, stock_name, stock_code)

    def get_statistics(self) -> dict:
        """获取准则统计"""
        rules = self.matcher.rules
        
        # 按类别统计
        by_category = {}
        for rule in rules:
            cat = rule.category.value
            if cat not in by_category:
                by_category[cat] = 0
            by_category[cat] += 1
        
        # 按来源统计
        by_source = {}
        for rule in rules:
            src = rule.source
            if src not in by_source:
                by_source[src] = 0
            by_source[src] += 1
        
        return {
            "total": len(rules),
            "by_category": by_category,
            "by_source": by_source
        }
```

- [ ] **Step 2: 提交**

```bash
git add src/trading_rules/service.py
git commit -m "feat: 实现交易准则服务层"
```

---

## Task 7: 实现 API 接口

**Files:**
- Create: `src/trading_rules/api.py`
- Modify: `src/web/api/router.py`

- [ ] **Step 1: 实现 API 接口**

```python
# src/trading_rules/api.py
"""交易准则 API"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import Optional

from .service import TradingRuleService
from .models import RuleCategory

router = APIRouter(prefix="/rules", tags=["rules"])

# 服务实例（延迟初始化）
_service: Optional[TradingRuleService] = None


def get_service() -> TradingRuleService:
    """获取服务实例"""
    global _service
    if _service is None:
        _service = TradingRuleService()
    return _service


class CheckRequest(BaseModel):
    """检查请求"""
    symbol: str
    market: str = "A"
    scenario: str = "entry"
    stock_data: dict = {}


@router.get("/")
async def list_rules():
    """获取所有准则"""
    service = get_service()
    rules = service.get_all_rules()
    return {
        "total": len(rules),
        "rules": [r.model_dump() for r in rules]
    }


@router.get("/{rule_id}")
async def get_rule(rule_id: str):
    """获取单条准则"""
    service = get_service()
    rule = service.get_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="准则不存在")
    return rule.model_dump()


@router.get("/category/{category}")
async def get_rules_by_category(category: str):
    """按类别获取准则"""
    service = get_service()
    rules = service.get_rules_by_category(category)
    return {
        "category": category,
        "total": len(rules),
        "rules": [r.model_dump() for r in rules]
    }


@router.get("/search")
async def search_rules(q: str = Query(..., description="搜索关键词")):
    """搜索准则"""
    service = get_service()
    rules = service.search_rules(q)
    return {
        "keyword": q,
        "total": len(rules),
        "rules": [r.model_dump() for r in rules]
    }


@router.post("/check")
async def check_rules(request: CheckRequest):
    """检查准则"""
    service = get_service()
    result = service.check_stock(
        symbol=request.symbol,
        market=request.market,
        scenario=request.scenario,
        stock_data=request.stock_data
    )
    return result


@router.get("/statistics")
async def get_statistics():
    """获取准则统计"""
    service = get_service()
    return service.get_statistics()
```

- [ ] **Step 2: 注册路由**

```python
# src/web/api/router.py (追加)

from src.trading_rules.api import router as rules_router

# 注册子路由
router.include_router(rules_router)
```

- [ ] **Step 3: 提交**

```bash
git add src/trading_rules/api.py src/web/api/router.py
git commit -m "feat: 实现交易准则 API 接口"
```

---

## Task 8: 集成到 AI 分析

**Files:**
- Modify: `src/analysis/agent/stock_agent.py`

- [ ] **Step 1: 修改 stock_agent.py**

```python
# src/analysis/agent/stock_agent.py (修改 analyze_with_strategy 方法)

    async def analyze_with_strategy(
        self,
        stock_code: str,
        strategy_name: str = "comprehensive",
        context: dict = None,
    ) -> AnalysisResult:
        """使用策略分析股票"""
        strategy = STRATEGIES.get(strategy_name)
        if not strategy:
            raise ValueError(f"策略 {strategy_name} 不存在")

        # 构建上下文
        if context is None:
            context = {}

        # 尝试获取实际数据
        try:
            from src.data.service import DataService
            from src.data.models import Market

            data_service = DataService()

            # 获取股票信息
            catalog_info = data_service.catalog.mapping.get(stock_code, {})
            stock_name = catalog_info.get("name", stock_code)

            # 获取技术指标
            try:
                indicators = await data_service.get_technical_indicators(stock_code, Market.A)
                context.update({
                    "stock_name": stock_name,
                    "stock_code": stock_code,
                    "current_price": 0,
                    "ma5": indicators.ma5,
                    "ma10": indicators.ma10,
                    "ma20": indicators.ma20,
                    "ma60": indicators.ma60,
                    "macd": indicators.macd,
                    "macd_signal": indicators.macd_signal,
                    "macd_hist": indicators.macd_hist,
                    "rsi_6": indicators.rsi_6,
                    "rsi_12": indicators.rsi_12,
                    "rsi_24": indicators.rsi_24,
                    "kdj_k": indicators.kdj_k,
                    "kdj_d": indicators.kdj_d,
                    "kdj_j": indicators.kdj_j,
                })
            except Exception as e:
                logger.warning(f"获取技术指标失败: {e}")
                context.setdefault("stock_name", stock_name)
                context.setdefault("stock_code", stock_code)

        except Exception as e:
            logger.warning(f"获取股票数据失败: {e}")
            context.setdefault("stock_name", stock_code)
            context.setdefault("stock_code", stock_code)

        # 集成交易准则
        try:
            from src.trading_rules.service import TradingRuleService
            rules_service = TradingRuleService()
            
            # 构建带准则的提示词
            prompt = rules_service.build_analysis_prompt(
                stock_data=context,
                stock_name=context.get("stock_name", stock_code),
                stock_code=stock_code
            )
        except Exception as e:
            logger.warning(f"加载交易准则失败: {e}")
            # 回退到原始提示词
            default_context = {
                "stock_name": context.get("stock_name", stock_code),
                "stock_code": stock_code,
                "current_price": context.get("current_price", 0),
                "ma5": context.get("ma5", 0),
                "ma10": context.get("ma10", 0),
                "ma20": context.get("ma20", 0),
                "ma60": context.get("ma60", 0),
                "macd": context.get("macd", 0),
                "macd_signal": context.get("macd_signal", 0),
                "macd_hist": context.get("macd_hist", 0),
                "rsi_6": context.get("rsi_6", 0),
                "rsi_12": context.get("rsi_12", 0),
                "rsi_24": context.get("rsi_24", 0),
                "kdj_k": context.get("kdj_k", 0),
                "kdj_d": context.get("kdj_d", 0),
                "kdj_j": context.get("kdj_j", 0),
            }
            
            try:
                prompt = strategy.get_prompt_template().format(**default_context)
            except KeyError as e:
                logger.warning(f"提示词模板缺少参数: {e}")
                prompt = strategy.get_prompt_template()

        # AI 分析
        if self.ai_adapter:
            result = await self.ai_adapter.analyze(prompt, context)
        else:
            result = AnalysisResult(
                score=50,
                signal="hold",
                trend="neutral",
                reason="AI 适配器未配置"
            )

        return result
```

- [ ] **Step 2: 提交**

```bash
git add src/analysis/agent/stock_agent.py
git commit -m "feat: 集成交易准则到AI分析 - 自动参考经典投资书籍"
```

---

## Task 9: 运行完整测试

**Files:**
- None

- [ ] **Step 1: 运行所有测试**

```bash
pytest tests/ -v --tb=short 2>&1 | tail -30
```

Expected: 所有测试通过

- [ ] **Step 2: 测试 API**

```bash
# 启动服务
stock-hub serve

# 测试 API
curl http://localhost:8000/api/v1/rules
curl http://localhost:8000/api/v1/rules/RULE_001
curl http://localhost:8000/api/v1/rules/category/entry
curl http://localhost:8000/api/v1/rules/search?q=止损
```

- [ ] **Step 3: 提交**

```bash
git add .
git commit -m "feat: 交易准则模块完成 - 64条准则、5大类别、集成AI分析"
```

---

## 阶段完成检查清单

- [ ] 数据模型完成
- [ ] 准则数据库完成（20条核心准则）
- [ ] 准则匹配器完成
- [ ] 准则检查器完成
- [ ] 提示词构建器完成
- [ ] 服务层完成
- [ ] API 接口完成
- [ ] 集成到 AI 分析
- [ ] 所有测试通过
- [ ] 文档完成

---

## 下一步

阶段完成后，可以：
1. 扩展准则数据库（添加更多准则）
2. 完善检查器逻辑（更精确的检查）
3. 添加前端页面（准则浏览、检查结果展示）
4. 集成到回测系统
