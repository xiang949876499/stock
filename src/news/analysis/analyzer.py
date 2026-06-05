"""舆情分析"""

from src.data.models import NewsItem
from src.news.processors.sentiment import analyze_sentiment
from src.infra.logger import get_logger

logger = get_logger("news_analyzer")


class NewsAnalyzer:
    """新闻分析器"""

    def __init__(self):
        pass

    def analyze(self, news_list: list[NewsItem]) -> dict:
        """分析新闻"""
        if not news_list:
            return {
                "sentiment": "neutral",
                "score": 50,
                "hotness": 0,
                "key_news": [],
            }

        # 情绪分析
        sentiment = analyze_sentiment(news_list)

        # 热度计算
        hotness = len(news_list)

        # 关键新闻提取
        key_news = sorted(
            news_list,
            key=lambda x: x.importance == "P0",
            reverse=True
        )[:5]

        return {
            "sentiment": sentiment["overall"],
            "score": sentiment["score"],
            "hotness": hotness,
            "key_news": [
                {
                    "title": n.title,
                    "source": n.source,
                    "sentiment": n.sentiment,
                }
                for n in key_news
            ],
        }
