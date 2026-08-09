import logging
from typing import Dict, List, Optional
from app.services.ai.service import AIService, ai_service

logger = logging.getLogger(__name__)


class ProactiveSuggestor:
    """
    Generates proactive suggestions based on user behavior,
    market conditions, and conversation context.
    """

    def __init__(self):
        self.ai_service = ai_service

    async def get_suggestions(
        self,
        user_id: int,
        current_context: Dict,
        market_data: Optional[Dict] = None,
    ) -> List[str]:
        """Generate contextual suggestions for the user."""
        suggestions = []

        if market_data:
            market_suggestions = self._market_based_suggestions(market_data)
            suggestions.extend(market_suggestions)

        user_profile = current_context.get("user_profile", {})
        if user_profile:
            profile_suggestions = self._profile_based_suggestions(user_profile)
            suggestions.extend(profile_suggestions)

        financial_ctx = current_context.get("financial_context", {})
        if financial_ctx.get("mentioned_companies"):
            company_suggestions = self._company_based_suggestions(
                financial_ctx["mentioned_companies"]
            )
            suggestions.extend(company_suggestions)

        return suggestions[:5]

    def _market_based_suggestions(self, market_data: Dict) -> List[str]:
        """Generate suggestions based on market conditions."""
        suggestions = []

        for name, data in market_data.items():
            change = data.get("change_percent", 0)
            if abs(change) > 2:
                direction = "up" if change > 0 else "down"
                suggestions.append(
                    f"Markets are {direction} significantly. Want me to analyze what's driving the move?"
                )
                break

        return suggestions

    def _profile_based_suggestions(self, profile: Dict) -> List[str]:
        """Generate suggestions based on user profile."""
        suggestions = []
        role = profile.get("role", "")
        sectors = profile.get("sectors", [])
        watchlist = profile.get("watchlist", [])

        if watchlist and len(watchlist) > 0:
            suggestions.append(
                f"Want me to check on your watchlist stocks ({', '.join(watchlist[:3])})?"
            )

        if role == "investor":
            suggestions.append("Interested in comparing valuations of your watchlist stocks?")
        elif role == "analyst":
            suggestions.append("Want a detailed financial analysis of any specific company?")

        return suggestions

    def _company_based_suggestions(self, companies: List[str]) -> List[str]:
        """Generate suggestions based on mentioned companies."""
        suggestions = []

        if len(companies) >= 2:
            suggestions.append(
                f"Want me to compare {companies[0]} and {companies[1]}?"
            )

        if companies:
            suggestions.append(
                f"Should I set up a price alert for {companies[0]}?"
            )

        return suggestions

    async def generate_follow_up_questions(
        self, response: str, intent: str, context: Dict
    ) -> List[str]:
        """Generate intelligent follow-up questions."""
        prompt = f"""Based on this financial assistant response, generate 2-3 relevant follow-up questions a user might ask.

Response: {response[:500]}
Intent: {intent}
Context: {str(context)[:300]}

Return only the questions, one per line, without numbering or bullets."""

        result = await self.ai_service.generate(
            prompt=prompt,
            temperature=0.5,
            max_tokens=200,
        )

        if result["success"]:
            lines = result["content"].strip().split("\n")
            return [q.strip() for q in lines if q.strip()][:3]

        return []


proactive_suggestor = ProactiveSuggestor()
