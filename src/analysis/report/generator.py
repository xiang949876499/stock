"""报告生成器"""

from datetime import datetime
from typing import Optional
from src.analysis.ai.base import AIModelAdapter
from src.infra.logger import get_logger

logger = get_logger("report_generator")


class ReportGenerator:
    """报告生成器"""

    def __init__(self, ai_adapter: Optional[AIModelAdapter] = None):
        self.ai_adapter = ai_adapter

    async def generate_decision_dashboard(
        self,
        stock_name: str,
        stock_code: str,
        score: float,
        signal: str,
        trend: str,
        reason: str,
        risk_alerts: list[str] = None,
        catalysts: list[str] = None,
        target_price: float = None,
        stop_loss: float = None,
    ) -> str:
        """生成决策仪表盘"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 信号标签
        signal_emoji = "🟢" if signal == "buy" else "🔴" if signal == "sell" else "🟡"
        signal_text = "买入" if signal == "buy" else "卖出" if signal == "sell" else "持有"

        # 趋势标签
        trend_text = "看多" if trend == "bullish" else "看空" if trend == "bearish" else "震荡"

        # 风险警报
        risk_section = ""
        if risk_alerts:
            risk_items = "\n".join(f"• {r}" for r in risk_alerts)
            risk_section = f"\n🚨 风险警报:\n{risk_items}"

        # 利好催化
        catalyst_section = ""
        if catalysts:
            catalyst_items = "\n".join(f"• {c}" for c in catalysts)
            catalyst_section = f"\n✨ 利好催化:\n{catalyst_items}"

        # 目标价位
        price_section = ""
        if target_price or stop_loss:
            price_items = []
            if target_price:
                price_items.append(f"目标价: {target_price}")
            if stop_loss:
                price_items.append(f"止损价: {stop_loss}")
            price_section = f"\n📊 操作建议\n{' | '.join(price_items)}"

        dashboard = f"""
🎯 {now} 决策仪表盘
{stock_name}({stock_code}) | 评分 {score} | {signal_emoji}{signal_text} | {trend_text}

📊 分析结果
{reason}
{risk_section}
{catalyst_section}
{price_section}

---
生成时间: {now}
"""
        return dashboard

    async def generate_market_review(
        self,
        indices: list[dict],
        sectors: list[dict],
        stats: dict = None,
    ) -> str:
        """生成大盘复盘"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 指数部分
        indices_section = "\n".join(
            f"• {idx.get('name', '')}: {idx.get('price', 0)} ({idx.get('change', '0%')})"
            for idx in indices
        ) if indices else "暂无数据"

        # 板块部分
        sectors_section = "\n".join(
            f"• {s.get('name', '')}: {s.get('change', '0%')}"
            for s in sectors
        ) if sectors else "暂无数据"

        # 市场统计
        stats_section = ""
        if stats:
            stats_section = f"""
📈 市场概况
上涨: {stats.get('up_count', 0)} | 下跌: {stats.get('down_count', 0)} | 涨停: {stats.get('limit_up', 0)} | 跌停: {stats.get('limit_down', 0)}
"""

        review = f"""
🎯 {now} 大盘复盘

📊 主要指数
{indices_section}
{stats_section}
🔥 板块表现
{sectors_section}

---
生成时间: {now}
"""
        return review
