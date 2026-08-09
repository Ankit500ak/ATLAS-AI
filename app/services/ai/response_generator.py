from typing import Dict, Any, List, Optional
from app.services.ai.service import AIService
from app.services.ai.model_router import ModelRouter
from app.services.ai.prompts import PromptTemplates
from app.services.ai.formatters import (
    format_stock_comparison,
    format_stock_analysis,
    format_watchlist_summary,
    format_market_overview,
)
import json
import logging

logger = logging.getLogger(__name__)


class ResponseGenerator:
    """
    Generates structured, personalized responses using AI models.
    """

    def __init__(self, ai_service: AIService, model_router: ModelRouter):
        self.ai = ai_service
        self.router = model_router

    async def generate(
        self,
        intent: str,
        user_message: str,
        context: Dict[str, Any],
        financial_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        model_info = self.router.route(intent)
        system_message = self._build_system_message(intent, context)
        prompt = self._build_prompt(intent, user_message, context, financial_data)

        result = await self.ai.generate(
            prompt=prompt,
            system_message=system_message,
            temperature=0.7,
            max_tokens=model_info["max_tokens"],
        )

        if not result["success"]:
            return self._fallback_response(intent, user_message)

        response_data = self._parse_response(result["content"])
        
        # Use structured formatters for stock-related intents
        if intent == "compare_companies" and financial_data:
            tickers = list(financial_data.keys())
            formatted = format_stock_comparison(financial_data, tickers)
            response_data["response"] = formatted
        elif intent == "stock_analysis" and financial_data:
            ticker = list(financial_data.keys())[0] if financial_data else "STOCK"
            formatted = format_stock_analysis(ticker, financial_data)
            response_data["response"] = formatted
        elif intent == "watchlist_query":
            stocks = context.get("watchlist_data", [])
            if stocks:
                formatted = format_watchlist_summary(stocks)
                response_data["response"] = formatted
        elif intent == "market_overview" and financial_data:
            formatted = format_market_overview(financial_data)
            response_data["response"] = formatted
        
        response_data["model_used"] = result["model"]
        response_data["tokens_used"] = result["tokens_used"]
        response_data["cost_estimate"] = result["cost_estimate"]

        return response_data

    def _build_system_message(self, intent: str, context: Dict) -> str:
        base = PromptTemplates.SYSTEM_PERSONA
        role = context.get("user_profile", {}).get("role", "finance_professional")
        role_guidance = {
            "investor": "\n\nFocus on investment potential, valuation, and market opportunities.",
            "analyst": "\n\nProvide detailed financial metrics, ratios, and comparative analysis.",
            "founder": "\n\nEmphasize business implications, growth potential, and strategic insights.",
            "student": "\n\nExplain concepts clearly and provide educational context.",
        }
        if intent == "earnings_analysis":
            return PromptTemplates.EARNINGS_SYSTEM
        elif intent == "compare_companies":
            return PromptTemplates.COMPARISON_SYSTEM
        elif intent == "analyze_document":
            return PromptTemplates.DOCUMENT_SYSTEM
        elif intent == "daily_briefing":
            return PromptTemplates.BRIEFING_SYSTEM
        return base + role_guidance.get(role, "")

    def _build_prompt(self, intent: str, user_message: str, context: Dict, financial_data: Optional[Dict]) -> str:
        parts = []
        profile = context.get("user_profile", {})
        if profile:
            parts.append(f"User Role: {profile.get('role', 'N/A')}")
            parts.append(f"Interests: {', '.join(profile.get('sectors', []))}")
            parts.append(f"Watchlist: {', '.join(profile.get('watchlist', [])[:10])}")

        if context.get("compressed_history"):
            parts.append(f"=== CONVERSATION HISTORY (from previous chats) ===\n{context['compressed_history'][:600]}\nUse this to provide continuity and remember user preferences.")

        if financial_data:
            parts.append(f"=== REAL-TIME FINANCIAL DATA ===")
            for key, val in financial_data.items():
                if isinstance(val, dict):
                    lines = [f"  {k}: {v}" for k, v in val.items() if v is not None]
                    parts.append(f"[{key}]\n" + "\n".join(lines[:15]))
                else:
                    parts.append(f"[{key}] {val}")
            parts.append("=== END DATA ===")

        parts.append(f"USER QUESTION: {user_message}")
        parts.append(f"""
Think step by step:
1. What is the user actually asking?
2. What does the data show?
3. WHY does this matter? (significance, implications, context)
4. What should they do next?

Be direct and concise. Explain the "so what" — why should they care about this data?""")
        return "\n\n".join(parts)

    def _parse_response(self, content: str) -> Dict[str, Any]:
        return {
            "response": content,
            "insights": self._extract_insights(content),
            "sources": [],
            "confidence": 0.85,
            "follow_up_questions": [],
        }

    def _extract_insights(self, content: str) -> List[str]:
        insights = []
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("•") or line.startswith("-") or line.startswith("*"):
                insights.append(line.lstrip("•-* ").strip())
        return insights[:5]

    def _fallback_response(self, intent: str, user_message: str) -> Dict[str, Any]:
        return {
            "response": "I'm experiencing some technical difficulties processing your request. Could you try rephrasing or asking again in a moment?",
            "insights": [],
            "sources": [],
            "confidence": 0.0,
            "follow_up_questions": [],
            "model_used": "fallback",
            "tokens_used": 0,
            "cost_estimate": 0,
        }
