"""插件模块"""

from .base import AnalysisPlugin
from .registry import PluginRegistry

# 注册内置插件
from .financial_analysis.dcf import DCFValuationPlugin
from .financial_analysis.comps import ComparableAnalysisPlugin
from .financial_analysis.screening import StockScreeningPlugin
from .equity_research.earnings import EarningsAnalysisPlugin

PluginRegistry.register(DCFValuationPlugin())
PluginRegistry.register(ComparableAnalysisPlugin())
PluginRegistry.register(StockScreeningPlugin())
PluginRegistry.register(EarningsAnalysisPlugin())

# 注册内置代理
from .agents import AgentRegistry, MarketResearcherAgent

AgentRegistry.register("market_researcher", MarketResearcherAgent)

__all__ = ["AnalysisPlugin", "PluginRegistry", "AgentRegistry"]
