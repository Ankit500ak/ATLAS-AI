from typing import Dict, Optional, List
from datetime import datetime
import logging
from app.core.di.container import ServiceContainer, get_container
from app.domain.services import StockService, MarketService, NewsService

logger = logging.getLogger(__name__)


class BriefingCompiler:
    """
    Compiles personalized daily market briefings for users.
    """

    def __init__(self, container: Optional[ServiceContainer] = None):
        self._container = container or get_container()
        self._stock_service = self._container.resolve(StockService)
        self._market_service = self._container.resolve(MarketService)
        self._news_service = self._container.resolve(NewsService)

    async def generate_briefing(self, user_id: int, summary_type: str = "morning") -> str:
        try:
            from app.database import async_session_factory
            from app.models.user import User
            from sqlalchemy import select

            user = None
            watchlist = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
            try:
                async with async_session_factory() as db:
                    result = await db.execute(select(User).where(User.telegram_id == user_id))
                    user = result.scalar_one_or_none()
                    if user and user.watchlist:
                        watchlist = user.watchlist
            except Exception as e:
                logger.error(f"Failed to load user for briefing {user_id}: {e}")

            market_status = {}
            indices = {}
            sector_perf = {}
            news = []

            try:
                market_status = await self._market_service.get_market_status()
            except Exception as e:
                logger.error(f"Failed to get market status: {e}")

            try:
                indices = await self._market_service.get_market_indices()
            except Exception as e:
                logger.error(f"Failed to get market indices: {e}")

            try:
                sector_perf = await self._stock_service.get_sector_performance()
            except Exception as e:
                logger.error(f"Failed to get sector performance: {e}")

            try:
                news = await self._news_service.get_market_news(limit=5)
            except Exception as e:
                logger.error(f"Failed to get market news: {e}")

            from app.utils.formatters import escape_markdown

            has_news = bool(news)
            has_market_moves = False
            if indices:
                for idx_data in indices.values():
                    if isinstance(idx_data, dict) and abs(idx_data.get("change_percent", 0)) > 1:
                        has_market_moves = True
                        break

            if summary_type == "morning" and not has_news and not has_market_moves:
                return None

            briefing = f"**Good {self._get_greeting(summary_type)}! Here's your Market Briefing**\n"
            briefing += f"_{datetime.now().strftime('%A, %B %d, %Y')}_\n\n"

            if indices:
                briefing += "**Market Overview**\n"
                for name, data in indices.items():
                    if isinstance(data, dict) and data.get("price") is not None and data.get("change") is not None:
                        emoji = "🟢" if data["change"] >= 0 else "🔴"
                        briefing += f"{emoji} {name}: {data['price']:,.2f} ({data['change']:+.2f} / {data.get('change_percent', 0):+.2f}%)\n"

            briefing += "\n**Your Watchlist**\n"
            for symbol in watchlist[:8]:
                try:
                    data = await self._stock_service.get_stock_data(symbol)
                    if data:
                        emoji = "🟢" if data["change"] >= 0 else "🔴"
                        briefing += (
                            f"{emoji} **{symbol}**: ${data['price']:.2f} "
                            f"({data['change']:+.2f} / {data['change_percent']:+.2f}%)\n"
                        )
                except Exception as e:
                    logger.error(f"Failed to get stock data for {symbol}: {e}")

            if news:
                briefing += "\n**Top News**\n"
                for article in news[:5]:
                    title = escape_markdown(article['title'][:80])
                    briefing += f"• {title}\n"

            status_text = market_status.get('status', 'unknown')
            briefing += f"\n_Market is currently {status_text}_"
            briefing += "\n\nAsk me anything about these stocks or market events!"

            return briefing

        except Exception as e:
            logger.error(f"Failed to generate briefing for user {user_id}: {e}", exc_info=True)
            return "I'm sorry, I couldn't generate your briefing right now. Please try again later."

    def _get_greeting(self, summary_type: str = "morning") -> str:
        if summary_type == "evening":
            return "Evening"
        hour = datetime.now().hour
        if hour < 12:
            return "Morning"
        elif hour < 17:
            return "Afternoon"
        else:
            return "Evening"