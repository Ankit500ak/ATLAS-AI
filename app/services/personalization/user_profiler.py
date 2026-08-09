from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)


class UserProfiler:
    """
    Dynamic user profiling that learns from every interaction.
    Tracks interests, patterns, and preferences over time.
    """

    INTENT_INTEREST_BOOST = {
        "research_company": 0.15,
        "earnings_analysis": 0.12,
        "compare_companies": 0.10,
        "portfolio_analysis": 0.15,
        "sec_filing": 0.08,
        "query_stock_price": 0.05,
        "market_news": 0.05,
    }

    async def update_from_interaction(
        self,
        user_id: int,
        message: str,
        response: str,
        intent: str,
        db: AsyncSession,
    ):
        result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return

        if not user.interests:
            user.interests = {"topics": {}, "companies": {}, "sectors": {}}
        if not user.usage_patterns:
            user.usage_patterns = {
                "peak_hours": [],
                "common_queries": [],
                "total_messages": 0,
            }

        self._update_topic_interests(user, intent, message)
        self._update_company_interests(user, message)
        self._update_usage_patterns(user, intent)
        self._update_response_preferences(user, response)

        user.last_active = datetime.now(timezone.utc)
        user.usage_patterns["total_messages"] = user.usage_patterns.get("total_messages", 0) + 1

        await db.commit()

    def _update_topic_interests(self, user: User, intent: str, message: str):
        topics = user.interests.get("topics", {})
        boost = self.INTENT_INTEREST_BOOST.get(intent, 0.03)
        intent_key = intent.replace("_", " ")

        if intent_key in topics:
            topics[intent_key] = min(topics[intent_key] + boost, 1.0)
        else:
            topics[intent_key] = boost

        decay = 0.98
        for topic in list(topics.keys()):
            if topic != intent_key:
                topics[topic] = max(topics[topic] * decay, 0.01)

        user.interests["topics"] = topics

    def _update_company_interests(self, user: User, message: str):
        import re
        known_symbols = {
            "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL",
            "amazon": "AMZN", "tesla": "TSLA", "nvidia": "NVDA",
            "meta": "META", "netflix": "NFLX", "amd": "AMD",
        }

        companies = user.interests.get("companies", {})
        message_lower = message.lower()

        for name, ticker in known_symbols.items():
            if name in message_lower:
                if ticker in companies:
                    companies[ticker] = min(companies[ticker] + 0.15, 1.0)
                else:
                    companies[ticker] = 0.15

        ticker_pattern = r'\b([A-Z]{2,5})\b'
        for match in re.findall(ticker_pattern, message):
            if match not in companies:
                companies[match] = 0.1
            else:
                companies[match] = min(companies[match] + 0.1, 1.0)

        decay = 0.95
        for ticker in list(companies.keys()):
            if ticker not in message:
                companies[ticker] = max(companies[ticker] * decay, 0.01)

        user.interests["companies"] = companies

    def _update_usage_patterns(self, user: User, intent: str):
        patterns = user.usage_patterns
        common = patterns.get("common_queries", [])

        intent_entry = next((e for e in common if e["intent"] == intent), None)
        if intent_entry:
            intent_entry["count"] = intent_entry.get("count", 0) + 1
        else:
            common.append({"intent": intent, "count": 1})

        common.sort(key=lambda x: x.get("count", 0), reverse=True)
        patterns["common_queries"] = common[:20]

        hour = datetime.now().hour
        peak_hours = patterns.get("peak_hours", [])
        if hour not in peak_hours:
            peak_hours.append(hour)
        patterns["peak_hours"] = peak_hours[-24:]

    def _update_response_preferences(self, user: User, response: str):
        prefs = user.response_preferences or {}
        if not prefs:
            prefs = {
                "length": "concise",
                "style": "professional",
                "include_charts": True,
                "include_sources": True,
            }

        response_len = len(response.split())
        if response_len < 100:
            detected_length = "concise"
        elif response_len < 300:
            detected_length = "detailed"
        else:
            detected_length = "comprehensive"

        prefs["last_detected_length"] = detected_length
        user.response_preferences = prefs

    async def get_user_summary(self, user_id: int, db: AsyncSession) -> Dict:
        result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return {}

        top_companies = sorted(
            user.interests.get("companies", {}).items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        top_topics = sorted(
            user.interests.get("topics", {}).items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return {
            "role": user.role,
            "sectors": user.sectors or [],
            "watchlist": user.watchlist or [],
            "top_companies": [c[0] for c in top_companies],
            "top_topics": [t[0] for t in top_topics],
            "briefing_time": user.briefing_time,
            "total_messages": user.usage_patterns.get("total_messages", 0),
            "last_active": user.last_active.isoformat() if user.last_active else None,
        }
