"""市场研究员代理"""

from typing import Any, Dict, List, Optional

from src.plugins.agents.base import AnalysisAgent
from src.plugins.base import AnalysisPlugin


MARKET_RESEARCHER_PROMPT = """
你是一位资深市场研究员，专注于 A 股和港股市场。

## 工作流程
1. **行业概览**: 分析行业规模、增长趋势、政策环境
2. **竞争格局**: 识别主要参与者、市场份额、竞争优势
3. **同行对比**: 使用可比公司分析法评估目标公司
4. **投资想法**: 基于分析提出投资建议

## 分析框架
- 使用 PESTEL 分析宏观环境
- 使用波特五力分析行业竞争
- 使用 SWOT 分析公司优劣势
- 使用 DCF 和相对估值法评估价值

## 输出格式
生成结构化的研究报告，包含：
- 行业概况
- 竞争格局
- 公司分析
- 估值分析
- 投资建议
- 风险提示
"""


class MarketResearcherAgent(AnalysisAgent):
    """市场研究员代理"""

    def __init__(
        self,
        ai_adapter: Any = None,
        plugins: Optional[List[AnalysisPlugin]] = None,
    ):
        super().__init__(ai_adapter, plugins)

    @property
    def system_prompt(self) -> str:
        return MARKET_RESEARCHER_PROMPT

    async def research(
        self,
        industry: str,
        symbol: str = None,
    ) -> Dict[str, Any]:
        """执行市场研究

        Args:
            industry: 行业名称
            symbol: 股票代码（可选）

        Returns:
            研究结果字典
        """
        context = {
            "industry": industry,
            "symbol": symbol,
        }

        query = f"研究 {industry} 行业"
        if symbol:
            query += f"，重点关注 {symbol}"

        return await self.run(query, context)
