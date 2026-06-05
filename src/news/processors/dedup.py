"""新闻去重"""

from src.data.models import NewsItem


def deduplicate_news(news_list: list[NewsItem]) -> list[NewsItem]:
    """新闻去重"""
    seen = set()
    unique_news = []

    for news in news_list:
        # 使用标题和来源作为唯一标识
        key = (news.title, news.source)
        if key not in seen:
            seen.add(key)
            unique_news.append(news)

    return unique_news
