import yfinance as yf
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)
executor = ThreadPoolExecutor(max_workers=4)


class NewsService:
    """
    Service for fetching financial news from Yahoo Finance and other sources.
    """

    def __init__(self):
        self._cache = {}
        self._cache_ttl = 900

    async def get_stock_news(self, symbol: str, limit: int = 5) -> List[Dict]:
        cache_key = f"news_{symbol}_{limit}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached["timestamp"]).total_seconds() < self._cache_ttl:
                return cached["data"]

        try:
            loop = asyncio.get_running_loop()
            ticker = await loop.run_in_executor(executor, lambda: yf.Ticker(symbol))
            news = await loop.run_in_executor(executor, lambda: ticker.news)

            if not news:
                return []

            articles = []
            for item in news[:limit]:
                try:
                    pub_time = item.get("providerPublishTime")
                    if pub_time and isinstance(pub_time, (int, float)):
                        published = datetime.fromtimestamp(pub_time).isoformat()
                    else:
                        published = datetime.now().isoformat()
                except (TypeError, ValueError):
                    published = datetime.now().isoformat()

                article = {
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "source": item.get("publisher", ""),
                    "url": item.get("link", ""),
                    "published_at": published,
                    "symbols": [symbol],
                }
                articles.append(article)

            self._cache[cache_key] = {"data": articles, "timestamp": datetime.now()}
            return articles

        except Exception as e:
            logger.error(f"Failed to fetch news for {symbol}: {e}")
            return []

    async def get_market_news(self, limit: int = 10) -> List[Dict]:
        cache_key = f"market_news_{limit}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if (datetime.now() - cached["timestamp"]).total_seconds() < self._cache_ttl:
                return cached["data"]

        try:
            loop = asyncio.get_running_loop()
            market = await loop.run_in_executor(executor, lambda: yf.Ticker("^GSPC"))
            news = await loop.run_in_executor(executor, lambda: market.news)

            if not news:
                return []

            articles = []
            for item in news[:limit]:
                try:
                    pub_time = item.get("providerPublishTime")
                    if pub_time and isinstance(pub_time, (int, float)):
                        published = datetime.fromtimestamp(pub_time).isoformat()
                    else:
                        published = datetime.now().isoformat()
                except (TypeError, ValueError):
                    published = datetime.now().isoformat()

                article = {
                    "title": item.get("title", ""),
                    "summary": item.get("summary", ""),
                    "source": item.get("publisher", ""),
                    "url": item.get("link", ""),
                    "published_at": published,
                    "symbols": [],
                }
                articles.append(article)

            self._cache[cache_key] = {"data": articles, "timestamp": datetime.now()}
            return articles

        except Exception as e:
            logger.error(f"Failed to fetch market news: {e}")
            return []

    async def get_trending_news(self) -> List[Dict]:
        trending_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META"]
        all_news = []
        for ticker in trending_tickers[:3]:
            news = await self.get_stock_news(ticker, limit=3)
            all_news.extend(news)
        seen_titles = set()
        unique_news = []
        for article in all_news:
            if article["title"] not in seen_titles:
                seen_titles.add(article["title"])
                unique_news.append(article)
        return unique_news[:10]

    async def get_earnings_news(self, symbols: List[str]) -> List[Dict]:
        all_news = []
        for symbol in symbols[:5]:
            news = await self.get_stock_news(symbol, limit=2)
            for article in news:
                article["category"] = "earnings"
            all_news.extend(news)
        return all_news
