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
