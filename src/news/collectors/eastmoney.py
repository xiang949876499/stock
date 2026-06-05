"""东方财富新闻采集"""

from datetime import datetime
from typing import Optional
import aiohttp
from bs4 import BeautifulSoup

from .base import NewsCollector
from src.data.models import Market, NewsItem
from src.infra.logger import get_logger

logger = get_logger("eastmoney")


class EastMoneyCollector(NewsCollector):
    """东方财富新闻采集器"""

    async def collect(
        self,
        symbol: str,
        market: Market,
        limit: int = 50
    ) -> list[NewsItem]:
        """采集新闻"""
        try:
            # 构建 URL
            if market == Market.A:
                url = f"https://guba.eastmoney.com/list,{symbol}.html"
            else:
                return []

            # 获取页面
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return []
                    html = await resp.text()

            # 解析页面
            soup = BeautifulSoup(html, 'html.parser')
            news_list = []

            # 提取新闻标题
            items = soup.select('.listitem .note')
            for item in items[:limit]:
                title_elem = item.select_one('.l3 a')
                if title_elem:
                    title = title_elem.text.strip()
                    news_item = NewsItem(
                        id=f"eastmoney_{symbol}_{len(news_list)}",
                        symbol=symbol,
                        market=market,
                        title=title,
                        content="",
                        source="eastmoney",
                        url=f"https://guba.eastmoney.com{title_elem.get('href', '')}",
                        publish_time=datetime.now(),
                        sentiment="neutral",
                        importance="P2",
                    )
                    news_list.append(news_item)

            return news_list

        except Exception as e:
            logger.error(f"东方财富新闻采集失败: {e}")
            return []
