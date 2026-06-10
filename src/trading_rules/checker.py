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
        # 根据准则ID进行检查
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
