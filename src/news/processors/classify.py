"""新闻分类"""

from src.data.models import NewsItem


def classify_sentiment(news: NewsItem) -> str:
    """分类情绪"""
    # 简单的关键词分类
    positive_keywords = ["利好", "上涨", "增长", "突破", "创新高", "买入", "增持"]
    negative_keywords = ["利空", "下跌", "下降", "跌破", "创新低", "卖出", "减持"]

    title = news.title.lower()

    for keyword in positive_keywords:
        if keyword in title:
            return "positive"

    for keyword in negative_keywords:
        if keyword in title:
            return "negative"

    return "neutral"


def classify_importance(news: NewsItem) -> str:
    """分类重要性"""
    # 简单的重要性分类
    important_keywords = ["财报", "业绩", "重组", "收购", "政策", "监管"]

    title = news.title

    for keyword in important_keywords:
        if keyword in title:
            return "P0"

    return "P2"
