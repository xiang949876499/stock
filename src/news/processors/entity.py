"""实体识别"""

import re
from src.data.models import NewsItem


def extract_entities(news: NewsItem) -> dict:
    """提取实体"""
    entities = {
        "stocks": [],
        "industries": [],
        "people": [],
        "events": [],
    }

    title = news.title

    # 提取股票代码
    stock_pattern = r'[0-9]{6}'
    stocks = re.findall(stock_pattern, title)
    entities["stocks"] = stocks

    # 提取行业关键词
    industry_keywords = ["科技", "医药", "金融", "消费", "新能源", "白酒"]
    for keyword in industry_keywords:
        if keyword in title:
            entities["industries"].append(keyword)

    # 提取事件关键词
    event_keywords = ["财报", "业绩", "重组", "收购", "政策"]
    for keyword in event_keywords:
        if keyword in title:
            entities["events"].append(keyword)

    return entities
