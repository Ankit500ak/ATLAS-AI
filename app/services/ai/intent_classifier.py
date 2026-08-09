from typing import Dict, List, Optional
import re
import json
import logging

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    AI-first intent classification with keyword fallback.
    Uses LLM to understand user intent with confidence scoring.
    """

    INTENTS = {
        "query_stock_price": {
            "description": "User wants to know the current price, trading value, or quote of a specific stock",
            "keywords": ["price", "stock", "trading", "current", "quote", "how much", "worth", "value", "share price"],
            "patterns": [
                r"(?:what is|what's|how much is|tell me) .*(?:stock|price|trading at|worth)",
                r"(?:show|get|check) .*(?:price|stock|quote)",
                r"\b[A-Z]{1,5}\b.*(?:price|stock)",
            ],
            "examples": [
                "What is Apple's stock price?",
                "How much is Tesla trading at?",
                "Get me the current price of MSFT",
            ],
        },
        "research_company": {
            "description": "User wants to learn about a company - its business, overview, profile, or general information",
            "keywords": ["research", "analyze", "company", "overview", "about", "tell me about", "information on", "profile"],
            "patterns": [
                r"(?:tell me about|research|analyze|information on|look up) .*(?:company|business|firm)?",
                r"(?:what is|who is) .*(?:company|business)?",
                r"(?:show|get) .*(?:company|business) .*(?:info|overview|profile)",
            ],
            "examples": [
                "Tell me about Apple",
                "Research Microsoft",
                "Give me an overview of Tesla",
            ],
        },
        "compare_companies": {
            "description": "User wants to compare two or more companies, stocks, or investments against each other",
            "keywords": ["compare", "versus", "vs", "better", "difference", "comparison", "contrast"],
            "patterns": [
                r"compare .*(?:and|with|vs|versus|to) .",
                r"(?:which is better|difference between) .*(?:and|or) .",
                r".*(?:vs|versus) .*",
            ],
            "examples": [
                "Compare Apple and Google",
                "MSFT vs GOOGL",
                "Which is better, Tesla or Rivian?",
            ],
        },
        "earnings_analysis": {
            "description": "User wants to analyze a company's earnings report, quarterly results, revenue, or financial performance",
            "keywords": ["earnings", "quarterly", "revenue", "profit", "financial results", "income", "eps"],
            "patterns": [
                r"(?:analyze|explain|summarize|show) .*(?:earnings|quarterly|revenue|results)",
                r"(?:how did|what were) .*(?:earnings|revenue|results)",
                r".*(?:earnings|10-q|quarterly report)",
            ],
            "examples": [
                "Analyze Apple's latest earnings",
                "What were Tesla's quarterly results?",
                "Show me Amazon's revenue",
            ],
        },
        "analyze_document": {
            "description": "User wants to analyze, summarize, or review an uploaded document, PDF, or report",
            "keywords": ["document", "report", "pdf", "file", "upload", "attachment", "annual report", "10-k"],
            "patterns": [
                r"(?:analyze|summarize|explain|review) .*(?:document|report|pdf|file)",
                r"(?:what does|tell me about) .*(?:document|report|pdf)",
                r"upload .*(?:document|report|pdf|file)",
            ],
            "examples": [
                "Analyze this annual report",
                "Summarize this PDF",
                "What does this document say?",
            ],
        },
        "portfolio_analysis": {
            "description": "User wants to analyze their entire portfolio, holdings, positions, or investment performance",
            "keywords": ["portfolio", "holdings", "positions", "investments", "my portfolio", "my holdings", "my investments"],
            "patterns": [
                r"(?:analyze|review|check|show) .*(?:portfolio|holdings|positions|my portfolio|my holdings)",
                r"(?:what are|show me) .*(?:my|current) .*(?:portfolio|holdings|stocks)",
                r"(?:how is|how's) .*(?:portfolio|watchlist)",
            ],
            "examples": [
                "Analyze my portfolio",
                "Show me my watchlist",
                "How are my holdings doing?",
            ],
        },
        "market_news": {
            "description": "User wants to see latest market news, financial updates, or current events affecting markets",
            "keywords": ["news", "happening", "today", "market", "update", "events", "today's"],
            "patterns": [
                r"(?:what's|what is) (?:happening|going on|new) .*(?:market|today|news)",
                r"(?:show|get|tell me) .*(?:news|update|events)",
                r"(?:market|stock|financial) .*(?:news|update)",
            ],
            "examples": [
                "What's happening in the market today?",
                "Show me the latest financial news",
                "Any market updates?",
            ],
        },
        "set_alert": {
            "description": "User wants to set up a price alert, notification, or reminder for a stock reaching a certain price or condition",
            "keywords": ["alert", "notify", "remind", "watch", "track", "monitor", "alarm"],
            "patterns": [
                r"(?:alert|notify|remind) me .*(?:when|if|at)",
                r"(?:set|create|make) .*(?:alert|notification|reminder)",
                r"(?:track|monitor|watch) .*(?:stock|price|company)",
            ],
            "examples": [
                "Alert me when Apple hits $200",
                "Track Tesla and notify me of big moves",
                "Set a price alert for MSFT",
            ],
        },
        "explain_concept": {
            "description": "User wants to understand a financial concept, term, or how something works in finance/investing",
            "keywords": ["explain", "what is", "how does", "meaning", "define", "help me understand"],
            "patterns": [
                r"(?:what is|what's|define|explain) .",
                r"(?:how does|how do) .*(?:work|function)",
                r"(?:help me understand|teach me about) .",
            ],
            "examples": [
                "What is P/E ratio?",
                "Explain market cap",
                "How does a bear market work?",
            ],
        },
        "sec_filing": {
            "description": "User wants to find, view, or analyze SEC filings like 10-K, 10-Q, 8-K, or proxy statements",
            "keywords": ["sec", "filing", "10-k", "10-q", "8-k", "proxy", "annual report", "sec.gov"],
            "patterns": [
                r"(?:analyze|summarize|show|get) .*(?:sec|10-k|10-q|8-k|filing)",
                r".*(?:sec|10-k|10-q|8-k) .*(?:filing|report|document)",
                r"(?:what did|find) .*(?:sec|filing)",
            ],
            "examples": [
                "Analyze Apple's latest SEC filing",
                "Show me Tesla's 10-K",
                "What's in Microsoft's latest 8-K?",
            ],
        },
        "macro_economic": {
            "description": "User wants information about macroeconomic factors like Fed rates, inflation, GDP, or economic conditions",
            "keywords": ["fed", "interest rate", "inflation", "gdp", "economic", "recession", "federal reserve", "cpi"],
            "patterns": [
                r"(?:what is|how is|impact of) .*(?:fed|interest rate|inflation|gdp|economy)",
                r"(?:federal reserve|fed) .*(?:doing|said|announce)",
                r"(?:economic|macro) .*(?:outlook|data|indicator)",
            ],
            "examples": [
                "What is the Fed doing with interest rates?",
                "How does inflation affect the market?",
                "Economic outlook for next quarter",
            ],
        },
        "daily_briefing": {
            "description": "User wants their personalized daily market briefing, morning summary, or start-of-day update",
            "keywords": ["briefing", "morning brief", "daily update", "daily summary", "start my day"],
            "patterns": [
                r"(?:give|send|show) me .*(?:briefing|summary|update)",
                r"(?:morning|daily) .*(?:briefing|summary|update)",
                r"(?:start|begin) .*(?:day|morning) .*(?:with|briefing)",
            ],
            "examples": [
                "Give me my morning briefing",
                "Send me a daily market summary",
                "Start my day with a briefing",
            ],
        },
        "view_watchlist": {
            "description": "User wants to see the list of stocks they are currently tracking or have on their watchlist",
            "keywords": ["watchlist", "my stocks", "my shares", "tracking list"],
            "patterns": [
                r"(?:show|view|check|what are|what's on|list) .*(?:watchlist|my stocks|tracking list)",
                r"(?:my|current) .*(?:watchlist|portfolio|stocks)",
                r"^(?:show|view|check|what|which)\b.*(?:watchlist|stocks|tracking)",
            ],
            "examples": [
                "Show me my watchlist",
                "What stocks am I tracking?",
                "Check my watchlist",
                "Which stocks are in my watchlist",
            ],
        },
        "add_to_watchlist": {
            "description": "User wants to add one or more stocks to their watchlist or tracking list, OR is asking HOW to add stocks",
            "keywords": ["add", "track", "follow", "include"],
            "patterns": [
                r"^add\s+",
                r"^track\s+",
                r"^follow\s+",
                r"(?:how (?:do i|can i|to)|want to|need to) .*(?:add|track|follow|include)",
                r"(?:add|track|follow|include) .*(?:to|in|my) .*(?:watchlist|portfolio|list)",
            ],
            "examples": [
                "How do I add stocks to my watchlist?",
                "Add NVDA to my watchlist",
                "I want to track Tesla",
                "How can I add more stocks?",
                "track NVIDIA",
                "follow AAPL",
            ],
        },
        "view_alerts": {
            "description": "User wants to see their active price alerts, notifications, or tracking conditions",
            "keywords": ["my alerts", "active alerts", "price alerts", "alert list"],
            "patterns": [
                r"(?:show|view|check|what are|what's) .*(?:alerts|notifications)",
                r"(?:my|active) .*(?:alerts|notifications)",
            ],
            "examples": [
                "Show me my alerts",
                "What alerts do I have?",
                "Check my active alerts",
            ],
        },
        "upcoming_earnings": {
            "description": "User wants to see upcoming earnings dates, earnings calendar, or when companies will report",
            "keywords": ["upcoming earnings", "earnings calendar", "earnings date", "next earnings"],
            "patterns": [
                r"(?:show|what|when|check) .*(?:upcoming|next|earnings|calendar)",
                r"(?:earnings|reporting) .*(?:this week|next week|coming|upcoming)",
            ],
            "examples": [
                "Show me upcoming earnings",
                "When is Apple reporting?",
                "What earnings are coming up?",
            ],
        },
        "system_status": {
            "description": "User is asking about the bot's status, health, or if it's working properly",
            "keywords": ["system status", "bot status", "how are you", "are you working"],
            "patterns": [
                r"(?:what's|how's|check) .*(?:status|system|health)",
                r"(?:are you|you) .*(?:working|alive|ok|up)",
            ],
            "examples": [
                "How are you doing?",
                "Check system status",
                "Are you working?",
            ],
        },
        "market_sentiment": {
            "description": "User wants to understand overall market mood, investor sentiment, bullish/bearish feelings",
            "keywords": ["sentiment", "mood", "feeling", "optimistic", "pessimistic", "bullish", "bearish", "fear", "greed"],
            "patterns": [
                r"(?:what's|how's|check) .*(?:sentiment|mood|feeling)",
                r"(?:market|investor) .*(?:sentiment|mood|feeling|confidence)",
                r"(?:are we|is the market) .*(?:bullish|bearish|optimistic|pessimistic)",
            ],
            "examples": [
                "What's the market sentiment?",
                "Are investors bullish or bearish?",
                "How's the market feeling today?",
            ],
        },
        "reset_profile": {
            "description": "User wants to reset their profile, start over, or redo the onboarding process",
            "keywords": ["reset", "restart", "start over", "redo", "re-do", "begin again"],
            "patterns": [
                r"(?:reset|restart|redo|re-do) .*(?:profile|onboarding|setup|account)",
                r"(?:start|begin) .*(?:over|again|anew)",
            ],
            "examples": [
                "Reset my profile",
                "Start over",
                "Redo onboarding",
            ],
        },
        "email_query": {
            "description": "User wants to check, search, or summarize their email messages",
            "keywords": ["email", "emails", "gmail", "inbox", "message", "messages"],
            "patterns": [
                r"(?:check|show|summarize|search|find) .*(?:email|gmail|inbox|message)",
                r"(?:any|what) .*(?:email|message) .*(?:from|about|regarding)",
                r"(?:my|the) .*(?:email|inbox|gmail)",
            ],
            "examples": [
                "Check my emails",
                "Any emails from Apple?",
                "Summarize my recent emails",
            ],
        },
        "calendar_query": {
            "description": "User wants to check their calendar, meetings, schedule, or upcoming appointments",
            "keywords": ["calendar", "meeting", "meetings", "schedule", "appointment", "event", "events"],
            "patterns": [
                r"(?:what|show|check|any) .*(?:meeting|calendar|schedule|appointment|event)",
                r"(?:my|upcoming) .*(?:meeting|schedule|calendar|event)",
                r"(?:do i have|what's on) .*(?:meeting|schedule|calendar)",
            ],
            "examples": [
                "What meetings do I have today?",
                "Show my calendar for this week",
                "Any upcoming meetings?",
            ],
        },
        "drive_query": {
            "description": "User wants to find, view, or search files in their Google Drive",
            "keywords": ["drive", "file", "files", "document", "documents"],
            "patterns": [
                r"(?:show|find|search|check) .*(?:drive|file|document)",
                r"(?:my|the) .*(?:drive|files|documents)",
                r"(?:what|any) .*(?:file|document)",
            ],
            "examples": [
                "Show my Google Drive files",
                "Find documents about earnings",
            ],
        },
        "sheets_query": {
            "description": "User wants to find, view, or analyze spreadsheets or Google Sheets",
            "keywords": ["spreadsheet", "sheet", "sheets", "workbook", "tab", "excel", "csv"],
            "patterns": [
                r"(?:show|find|search|check|analyze) .*(?:sheet|spreadsheet|workbook|excel|csv)",
                r"(?:my|the) .*(?:sheet|spreadsheet|data|table)",
            ],
            "examples": [
                "Show me my spreadsheets",
                "Analyze this Google Sheet",
                "Check my financial data sheet",
            ],
        },
        "general_question": {
            "description": "General question that doesn't fit other categories, or greeting, or off-topic",
            "keywords": [],
            "patterns": [],
            "examples": [],
        },
    }

    def classify_keyword(self, message: str) -> Dict[str, float]:
        message_lower = message.lower()
        scores = {}

        for intent, config in self.INTENTS.items():
            if intent == "general_question":
                continue
            score = 0.0
            for keyword in config["keywords"]:
                if keyword in message_lower:
                    score += 0.3
            for pattern in config["patterns"]:
                if re.search(pattern, message_lower):
                    score += 0.4
            if score > 0:
                scores[intent] = min(score, 1.0)

        return scores

    def classify(self, message: str, use_ai: bool = False, ai_service=None) -> Dict:
        if use_ai and ai_service:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    return self.classify_keyword_sync(message)
                else:
                    return loop.run_until_complete(self._classify_with_ai(message, ai_service))
            except Exception:
                return self.classify_keyword_sync(message)
        return self.classify_keyword_sync(message)

    def classify_keyword_sync(self, message: str) -> Dict:
        keyword_scores = self.classify_keyword(message)

        if keyword_scores:
            best_intent = max(keyword_scores.items(), key=lambda x: x[1])
            if best_intent[1] >= 0.5:
                return {
                    "intent": best_intent[0],
                    "confidence": best_intent[1],
                    "complexity": self.INTENTS[best_intent[0]].get("complexity", 0.5),
                    "method": "keyword",
                    "all_scores": keyword_scores,
                }

        if keyword_scores:
            best_intent = max(keyword_scores.items(), key=lambda x: x[1])
            return {
                "intent": best_intent[0],
                "confidence": best_intent[1],
                "complexity": self.INTENTS[best_intent[0]].get("complexity", 0.5),
                "method": "keyword_fallback",
                "all_scores": keyword_scores,
            }

        return {
            "intent": "general_question",
            "confidence": 0.5,
            "complexity": 0.3,
            "method": "default",
            "all_scores": {},
        }

    async def classify_async(self, message: str, ai_service=None) -> Dict:
        if ai_service:
            return await self._classify_with_ai(message, ai_service)
        return self.classify_keyword_sync(message)

    async def _classify_with_ai(self, message: str, ai_service) -> Dict:
        intents_list = []
        for name, config in self.INTENTS.items():
            if name == "general_question":
                continue
            desc = config.get("description", "")
            examples = config.get("examples", [])[:2]
            intents_list.append(f"- {name}: {desc}")
            if examples:
                intents_list.append(f"  Examples: {json.dumps(examples)}")

        intents_text = "\n".join(intents_list)

        prompt = f"""You are an intent classifier for a financial assistant bot.

The user sent this message: "{message}"

Classify the user's INTENT into ONE of these categories:

{intents_text}

IMPORTANT RULES:
1. Focus on what the user WANTS TO DO, not just keywords they use
2. "How do I add stocks?" = add_to_watchlist (they want to learn to add)
3. "Add NVDA" = add_to_watchlist (they want to add a stock)
4. "Show my watchlist" = view_watchlist (they want to see their list)
5. "How to add" questions = the action they want to perform, not explanation

Return ONLY valid JSON with these fields:
- intent: the exact intent name from the list above
- confidence: a number from 0.0 to 1.0 showing how sure you are
- reasoning: brief explanation of why you chose this intent

Example response:
{{"intent": "add_to_watchlist", "confidence": 0.95, "reasoning": "User is asking how to add stocks to watchlist"}}"""

        result = await ai_service.generate_structured(prompt=prompt, temperature=0.1)
        data = result.get("data", {})

        intent = data.get("intent", "general_question")
        if intent not in self.INTENTS:
            intent = "general_question"

        confidence = data.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        confidence = max(0.0, min(1.0, float(confidence)))

        return {
            "intent": intent,
            "confidence": confidence,
            "complexity": self.INTENTS[intent].get("complexity", 0.5),
            "method": "ai",
            "reasoning": data.get("reasoning", ""),
            "all_scores": {},
        }
