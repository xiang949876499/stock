"""投资组合管理代理"""

from typing import Any, Dict, List, Optional

from src.plugins.agents.base import AnalysisAgent
from src.plugins.base import AnalysisPlugin


PORTFOLIO_MANAGER_PROMPT = """
你是一位专业的投资组合经理，专注于 A 股和港股市场。

## 工作流程
1. **组合分析**: 分析当前持仓的风险收益特征
2. **资产配置**: 根据风险偏好推荐资产配置
3. **再平衡建议**: 识别偏离目标配置的资产
4. **风险管理**: 监控组合风险指标

## 分析框架
- 现代投资组合理论 (MPT)
- 风险平价模型
- 因子投资模型
- 动态资产配置

## 输出格式
生成结构化的投资组合报告，包含：
- 组合概况
- 持仓分析
- 风险指标
- 配置建议
- 再平衡建议
"""


class PortfolioManagerAgent(AnalysisAgent):
    """投资组合管理代理"""

    def __init__(
        self,
        ai_adapter: Any = None,
        plugins: Optional[List[AnalysisPlugin]] = None,
    ):
        super().__init__(ai_adapter, plugins)

    @property
    def system_prompt(self) -> str:
        return PORTFOLIO_MANAGER_PROMPT

    async def analyze_portfolio(
        self,
        holdings: List[Dict[str, Any]],
        risk_profile: str = "moderate",
    ) -> Dict[str, Any]:
        """分析投资组合

        Args:
            holdings: 持仓列表，每项包含股票代码、数量、成本等
            risk_profile: 风险偏好 (conservative/moderate/aggressive)

        Returns:
            分析结果字典
        """
        context = {
            "holdings": holdings,
            "risk_profile": risk_profile,
        }
        return await self.run(
            f"分析投资组合，风险偏好: {risk_profile}",
            context,
        )

    async def suggest_allocation(
        self,
        total_capital: float,
        risk_profile: str = "moderate",
    ) -> Dict[str, Any]:
        """建议资产配置

        Args:
            total_capital: 总资金
            risk_profile: 风险偏好 (conservative/moderate/aggressive)

        Returns:
            配置建议结果字典
        """
        context = {
            "total_capital": total_capital,
            "risk_profile": risk_profile,
        }
        return await self.run(
            f"建议资产配置方案，总资金: {total_capital}，风险偏好: {risk_profile}",
            context,
        )
