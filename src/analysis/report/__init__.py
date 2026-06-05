"""报告生成"""

from .generator import ReportGenerator
from .templates import DECISION_DASHBOARD_TEMPLATE, MARKET_REVIEW_TEMPLATE

__all__ = [
    "ReportGenerator",
    "DECISION_DASHBOARD_TEMPLATE",
    "MARKET_REVIEW_TEMPLATE",
]
