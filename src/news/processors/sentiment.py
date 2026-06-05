"""情绪分析"""

from src.data.models import NewsItem


def analyze_sentiment(news_list: list[NewsItem]) -> dict:
    """分析情绪"""
    if not news_list:
        return {
            "overall": "neutral",
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "score": 50,
        }

    positive_count = sum(1 for n in news_list if n.sentiment == "positive")
    negative_count = sum(1 for n in news_list if n.sentiment == "negative")
    neutral_count = sum(1 for n in news_list if n.sentiment == "neutral")

    # 计算分数
    total = len(news_list)
    score = 50 + (positive_count - negative_count) / total * 50
    score = max(0, min(100, score))

    # 判断整体情绪
    if score > 60:
        overall = "positive"
    elif score < 40:
        overall = "negative"
    else:
        overall = "neutral"

    return {
        "overall": overall,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "score": round(score, 2),
    }
