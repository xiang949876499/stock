"""报告模板"""

# 决策仪表盘模板
DECISION_DASHBOARD_TEMPLATE = """
🎯 {date} 决策仪表盘
{stock_name}({stock_code}) | 评分 {score} | {signal} | {trend}

📰 重要信息速览
{key_news}

🚨 风险警报
{risk_alerts}

✨ 利好催化
{catalysts}

📊 操作建议
目标价: {target_price} | 止损: {stop_loss}

✅ 操作检查清单
{checklist}

---
生成时间: {generated_at}
"""

# 大盘复盘模板
MARKET_REVIEW_TEMPLATE = """
🎯 {date} 大盘复盘

📊 主要指数
{indices}

📈 市场概况
{market_stats}

🔥 板块表现
{sectors}

---
生成时间: {generated_at}
"""
