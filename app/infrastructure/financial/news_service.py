from app.domain.services import NewsService
from typing import List, Dict, Any
import logging
import feedparser
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class NewsServiceImpl(NewsService):
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 600
        self._feeds = [
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^DJI&region=US&lang=en-US",
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^IXIC&region=US&lang=en-US",
            "https://www.marketwatch.com/rss/topstories",
            "https://www.investing.com/rss/news_25.rss",
        ]

    async def get_market_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        cache_key = f"market_news_{limit}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached["timestamp"]).total_seconds() < self._cache_ttl:
                return cached["data"]

        try:
            all_news = []
            for feed_url in self._feeds:
                try:
                    parsed = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: feedparser.parse(feed_url)
                    )
                    for entry in parsed.entries[:limit]:
                        all_news.append({
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "summary": entry.get("summary", "")[:300],
                            "published": entry.get("published", ""),
                            "source": parsed.feed.get("title", "Unknown"),
                        })
                except Exception as e:
                    logger.debug(f"Failed to parse feed {feed_url}: {e}")

            all_news.sort(key=lambda x: x.get("published", ""), reverse=True)
            result = all_news[:limit]

            self._cache[cache_key] = {"data": result, "timestamp": datetime.now()}
            return result

        except Exception as e:
            logger.error(f"Failed to fetch market news: {e}")
            return []

    async def get_company_news(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        cache_key = f"company_news_{symbol}_{limit}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached["timestamp"]).total_seconds() < self._cache_ttl:
                return cached["data"]

        try:
            feed_url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
            parsed = await asyncio.get_event_loop().run_in_executor(
                None, lambda: feedparser.parse(feed_url)
            )

            news = []
            for entry in parsed.entries[:limit]:
                news.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:300],
                    "published": entry.get("published", ""),
                    "source": parsed.feed.get("title", symbol),
                })

            self._cache[cache_key] = {"data": news, "timestamp": datetime.now()}
            return news

        except Exception as e:
            logger.error(f"Failed to fetch company news for {symbol}: {e}")
            return []

    async def get_trending_news(self) -> List[Dict[str, Any]]:
        return await self.get_market_news(limit=5)