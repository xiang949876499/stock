"""新闻处理测试"""

import pytest
from datetime import datetime
from src.data.models import NewsItem, Market
from src.news.processors.dedup import deduplicate_news
from src.news.processors.classify import classify_sentiment, classify_importance
from src.news.processors.sentiment import analyze_sentiment
from src.news.processors.entity import extract_entities


@pytest.fixture
def sample_news():
    """样本新闻"""
    return [
        NewsItem(
            id="1",
            symbol="600519",
            market=Market.A,
            title="贵州茅台发布利好财报",
            content="...",
            source="eastmoney",
            url="https://example.com/1",
            publish_time=datetime(2026, 1, 1),
            sentiment="positive",
            importance="P0",
        ),
        NewsItem(
            id="2",
            symbol="600519",
            market=Market.A,
            title="贵州茅台股价下跌",
            content="...",
            source="sina",
            url="https://example.com/2",
            publish_time=datetime(2026, 1, 2),
            sentiment="negative",
            importance="P1",
        ),
        NewsItem(
            id="3",
            symbol="600519",
            market=Market.A,
            title="贵州茅台发布利好财报",  # 重复
            content="...",
            source="eastmoney",
            url="https://example.com/3",
            publish_time=datetime(2026, 1, 3),
            sentiment="positive",
            importance="P0",
        ),
    ]


def test_deduplicate_news(sample_news):
    """测试新闻去重"""
    unique = deduplicate_news(sample_news)
    assert len(unique) == 2  # 去掉一条重复的


def test_classify_sentiment():
    """测试情绪分类"""
    news = NewsItem(
        id="1",
        symbol="600519",
        market=Market.A,
        title="贵州茅台发布利好财报",
        content="...",
        source="eastmoney",
        url="https://example.com",
        publish_time=datetime(2026, 1, 1),
        sentiment="neutral",
        importance="P2",
    )
    assert classify_sentiment(news) == "positive"


def test_classify_sentiment_negative():
    """测试负面情绪分类"""
    news = NewsItem(
        id="1",
        symbol="600519",
        market=Market.A,
        title="贵州茅台股价下跌",
        content="...",
        source="eastmoney",
        url="https://example.com",
        publish_time=datetime(2026, 1, 1),
        sentiment="neutral",
        importance="P2",
    )
    assert classify_sentiment(news) == "negative"


def test_classify_importance():
    """测试重要性分类"""
    news = NewsItem(
        id="1",
        symbol="600519",
        market=Market.A,
        title="贵州茅台发布财报",
        content="...",
        source="eastmoney",
        url="https://example.com",
        publish_time=datetime(2026, 1, 1),
        sentiment="neutral",
        importance="P2",
    )
    assert classify_importance(news) == "P0"


def test_analyze_sentiment(sample_news):
    """测试情绪分析"""
    result = analyze_sentiment(sample_news)
    assert "overall" in result
    assert "positive_count" in result
    assert "negative_count" in result
    assert "score" in result


def test_analyze_sentiment_empty():
    """测试空新闻情绪分析"""
    result = analyze_sentiment([])
    assert result["overall"] == "neutral"
    assert result["score"] == 50


def test_extract_entities():
    """测试实体提取"""
    news = NewsItem(
        id="1",
        symbol="600519",
        market=Market.A,
        title="贵州茅台发布财报，科技板块上涨",
        content="...",
        source="eastmoney",
        url="https://example.com",
        publish_time=datetime(2026, 1, 1),
        sentiment="neutral",
        importance="P0",
    )
    entities = extract_entities(news)
    assert "stocks" in entities
    assert "industries" in entities
    assert "科技" in entities["industries"]
