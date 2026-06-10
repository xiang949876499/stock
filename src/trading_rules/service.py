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
