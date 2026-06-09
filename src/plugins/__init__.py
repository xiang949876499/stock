"""插件模块"""

from .base import AnalysisPlugin
from .registry import PluginRegistry

# 注册内置插件
from .financial_analysis.dcf import DCFValuationPlugin
from .financial_analysis.comps import ComparableAnalysisPlugin
from .financial_analysis.screening import StockScreeningPlugin
from .financial_analysis.lbo import LBOAnalysisPlugin
from .financial_analysis.ddm import DDMValuationPlugin
from .financial_analysis.merger import MergerAnalysisPlugin
from .equity_research.earnings import EarningsAnalysisPlugin
from .equity_research.one_pager import OnePagerPlugin

PluginRegistry.register(DCFValuationPlugin())
PluginRegistry.register(ComparableAnalysisPlugin())
PluginRegistry.register(StockScreeningPlugin())
PluginRegistry.register(LBOAnalysisPlugin())
PluginRegistry.register(DDMValuationPlugin())
PluginRegistry.register(MergerAnalysisPlugin())
PluginRegistry.register(EarningsAnalysisPlugin())
PluginRegistry.register(OnePagerPlugin())

# 注册内置代理
from .agents import AgentRegistry, MarketResearcherAgent, EarningsReviewerAgent

AgentRegistry.register("market_researcher", MarketResearcherAgent)
AgentRegistry.register("earnings_reviewer", EarningsReviewerAgent)

__all__ = ["AnalysisPlugin", "PluginRegistry", "AgentRegistry"]
