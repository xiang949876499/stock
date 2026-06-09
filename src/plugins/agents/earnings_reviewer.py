"""财报分析代理"""

from typing import Any, Dict, List, Optional

from src.plugins.agents.base import AnalysisAgent
from src.plugins.base import AnalysisPlugin


EARNINGS_REVIEWER_PROMPT = """
你是一位专业的财报分析师，专注于 A 股和港股公司财报分析。

## 工作流程
1. **获取财报**: 获取最新财报数据
2. **指标分析**: 分析关键财务指标变化
3. **对比分析**: 与历史数据和预期对比
4. **生成报告**: 生成研报草稿

## 分析重点
- 收入增长趋势
- 毛利率和净利率变化
- 现金流状况
- 资产负债表健康度
- 管理层展望

## 输出格式
生成结构化的财报分析报告，包含：
- 财报摘要
- 关键指标分析
- 同比/环比对比
- 投资建议
- 风险提示
"""


class EarningsReviewerAgent(AnalysisAgent):
    """财报分析代理"""

    def __init__(
        self,
        ai_adapter: Any = None,
        plugins: Optional[List[AnalysisPlugin]] = None,
    ):
        super().__init__(ai_adapter, plugins)

    @property
    def system_prompt(self) -> str:
        return EARNINGS_REVIEWER_PROMPT

    async def analyze(self, symbol: str, period: str) -> Dict[str, Any]:
        """分析财报

        Args:
            symbol: 股票代码
            period: 财报期间（如 2024Q3）

        Returns:
            分析结果字典
        """
        context = {
            "symbol": symbol,
            "period": period,
        }
        return await self.run(
            f"分析 {symbol} {period} 财报",
            context,
        )
