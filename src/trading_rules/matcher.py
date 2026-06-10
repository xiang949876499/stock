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
