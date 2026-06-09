"""风险管理代理"""

from typing import Any, Dict, List, Optional

from src.plugins.agents.base import AnalysisAgent
from src.plugins.base import AnalysisPlugin


RISK_MANAGER_PROMPT = """
你是一位专业的风险管理专家，专注于 A 股和港股市场。

## 工作流程
1. **风险识别**: 识别投资组合的各类风险
2. **风险量化**: 计算 VaR、CVaR、波动率等风险指标
3. **风险监控**: 监控市场风险、信用风险、流动性风险
4. **风险报告**: 生成风险评估报告

## 分析框架
- Value at Risk (VaR)
- Conditional VaR (CVaR)
- 压力测试
- 情景分析
- 风险因子分析

## 输出格式
生成结构化的风险评估报告，包含：
- 风险概况
- 风险指标
- 风险来源
- 风险建议
- 压力测试结果
"""


class RiskManagerAgent(AnalysisAgent):
    """风险管理代理"""

    def __init__(
        self,
        ai_adapter: Any = None,
        plugins: Optional[List[AnalysisPlugin]] = None,
    ):
        super().__init__(ai_adapter, plugins)

    @property
    def system_prompt(self) -> str:
        return RISK_MANAGER_PROMPT

    async def assess_portfolio_risk(
        self,
        holdings: List[Dict[str, Any]],
        confidence_level: float = 0.95,
    ) -> Dict[str, Any]:
        """评估投资组合风险

        Args:
            holdings: 持仓列表，每个元素包含 symbol、weight 等信息
            confidence_level: VaR 置信水平，默认 0.95

        Returns:
            风险评估结果字典
        """
        context = {
            "holdings": holdings,
            "confidence_level": confidence_level,
        }
        return await self.run(
            f"评估投资组合风险，置信水平: {confidence_level}",
            context,
        )

    async def stress_test(
        self,
        holdings: List[Dict[str, Any]],
        scenarios: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """执行压力测试

        Args:
            holdings: 持仓列表
            scenarios: 压力测试场景列表

        Returns:
            压力测试结果字典
        """
        context = {
            "holdings": holdings,
            "scenarios": scenarios,
        }
        return await self.run("执行投资组合压力测试", context)
