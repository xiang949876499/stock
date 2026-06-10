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