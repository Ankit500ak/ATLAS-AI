import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.core.di.container import ServiceContainer
from app.domain.services import NewsService, AIService

logger = logging.getLogger(__name__)


class NewsAggregator:
    """
    Aggregates and processes financial news from multiple sources.
    Runs in background to keep news cache fresh.
    """

    def __init__(self, container: ServiceContainer):
        self._container = container
        self._news_service = container.resolve(NewsService)
        self._ai_service = container.resolve(AIService)
        self._cache = {}
        self._cache_ttl = 900

    async def aggregate_news(self) -> List[Dict]:
        """Aggregate news from multiple sources."""
        try:
            market_news = await self._news_service.get_market_news(limit=10)
            trending_news = await self._news_service.get_trending_news()

            all_news = market_news + trending_news
            unique_news = self._deduplicate_news(all_news)
            enriched_news = await self._enrich_news(unique_news)

            self._cache = {
                "news": enriched_news,
                "timestamp": datetime.now(),
            }

            logger.info(f"Aggregated {len(enriched_news)} news articles")
            return enriched_news

        except Exception as e:
            logger.error(f"News aggregation failed: {e}")
            return []

    def _deduplicate_news(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate news articles."""
        seen_titles = set()
        unique = []
        for article in articles:
            title = article.get("title", "")
            if title not in seen_titles:
                seen_titles.add(title)
                unique.append(article)
        return unique

    async def _enrich_news(self, articles: List[Dict]) -> List[Dict]:
        """Enrich news articles with sentiment and relevance."""
        for article in articles[:10]:
            try:
                sentiment = await self._ai_service.analyze_sentiment(
                    article.get("title", "") + " " + article.get("summary", "")
                )
                article["sentiment"] = sentiment
                article["category"] = self._categorize_article(article)
            except Exception as e:
                logger.error(f"Failed to enrich article: {e}")
                article["sentiment"] = 0.0
                article["category"] = "general"

        return articles

    def _categorize_article(self, article: Dict) -> str:
        """Categorize news article based on content."""
        title = article.get("title", "").lower()
        summary = article.get("summary", "").lower()
        text = title + " " + summary

        categories = {
            "earnings": ["earnings", "revenue", "profit", "quarterly", "eps"],
            "merger": ["merger", "acquisition", "buyout", "deal"],
            "regulatory": ["sec", "regulation", "lawsuit", "fine", "investigation"],
            "macro": ["fed", "interest rate", "inflation", "gdp", "recession"],
            "ipo": ["ipo", "public offering", "listing"],
            "dividend": ["dividend", "payout", "yield"],
        }

        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return "general"

    def get_cached_news(self) -> List[Dict]:
        """Get cached news articles."""
        if self._cache and self._cache.get("timestamp"):
            age = (datetime.now() - self._cache["timestamp"]).seconds
            if age < self._cache_ttl:
                return self._cache.get("news", [])
        return []