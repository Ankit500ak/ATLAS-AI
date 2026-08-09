from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.ai.service import AIService
from app.services.ai.model_router import ModelRouter
from app.services.ai.intent_classifier import IntentClassifier
from app.services.ai.response_generator import ResponseGenerator
from app.services.ai.prompts import PromptTemplates
from app.services.ai.follow_up_loader import get_follow_ups
from app.services.conversation.context_manager import ContextManager
from app.services.financial.stock_service import StockService
from app.services.financial.market_service import MarketService
from app.services.financial.news_service import NewsService
from app.services.financial.sec_edgar_service import sec_edgar_service
from app.services.financial.earnings_calendar import earnings_calendar
from app.services.personalization.user_profiler import UserProfiler
from app.services.personalization.watchlist_manager import watchlist_manager
from app.services.personalization.proactive_suggestor import proactive_suggestor
from app.services.financial.cache_service import cache_service
import json
import re
import logging
import time

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Main orchestrator that coordinates all AI subsystems:
    - Intent classification
    - Context assembly
    - Financial data retrieval
    - Response generation
    - Proactive suggestions
    - Cache management
    """

    def __init__(self):
        self.ai_service = AIService()
        self.model_router = ModelRouter()
        self.intent_classifier = IntentClassifier()
        self.response_generator = ResponseGenerator(self.ai_service, self.model_router)
        self.context_manager = ContextManager()
        self.stock_service = StockService()
        self.news_service = NewsService()
        self.user_profiler = UserProfiler()

    def _md_to_html(self, text: str) -> str:
        """Convert markdown to HTML for Telegram."""
        if not text:
            return text
        # Convert **bold** to <b>bold</b>
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        # Convert *italic* to <i>italic</i> (but not inside <b> tags)
        text = re.sub(r'(?<!<b>)\*(.+?)\*(?!</b>)', r'<i>\1</i>', text)
        # Convert `code` to <code>code</code>
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        # Convert bullet points
        text = re.sub(r'^\s*[-•]\s+', '  • ', text, flags=re.MULTILINE)
        return text

    async def process_message(
        self,
        user_id: int,
        message: str,
        db: AsyncSession,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        start_time = time.time()

        try:
            from app.models.user import User
            from sqlalchemy import select
            result = await db.execute(select(User).where(User.telegram_id == user_id))
            user = result.scalar_one_or_none()

            if user and not user.onboarding_completed and user.onboarding_step < 6:
                return await self._handle_onboarding(user_id, message, db)

            if not user:
                new_user = User(telegram_id=user_id, onboarding_step=0)
                db.add(new_user)
                await db.commit()
                return await self._handle_onboarding(user_id, message, db)

            try:
                classification = await self.intent_classifier.classify_async(
                    message, ai_service=self.ai_service
                )
                intent = classification["intent"]
                confidence = classification["confidence"]
                logger.info(f"AI intent classified: {intent} (confidence={confidence:.2f}, method={classification.get('method')})")
            except Exception as e:
                logger.warning(f"AI classification failed, using keyword fallback: {e}")
                classification = self.intent_classifier.classify_keyword_sync(message)
                intent = classification["intent"]
                confidence = classification["confidence"]

            logger.info(f"Intent classified: {intent} (confidence={confidence:.2f})")

            context = await self.context_manager.build_context(
                user_id=user_id,
                new_message=message,
                db=db,
                conversation_id=conversation_id,
            )

            # Detect ambiguous queries and ask clarifying questions
            if intent == "general_question" and confidence < 0.7:
                symbols = self._extract_symbols(message)
                if symbols and self._is_ambiguous_query(message):
                    return await self._ask_clarifying_question(message, symbols[0])

            if intent == "sec_filing":
                return await self._handle_sec_filing(user_id, message, context)

            if intent == "set_alert":
                return await self._handle_set_alert(user_id, message, db)

            if intent == "daily_briefing":
                return await self._handle_daily_briefing(user_id)

            if intent == "portfolio_analysis":
                return await self._handle_portfolio_analysis(user_id, context)

            if intent == "email_query":
                return await self._handle_email_query(user_id, message, context)

            if intent == "calendar_query":
                return await self._handle_calendar_query(user_id, message, context)

            if intent == "drive_query":
                return await self._handle_drive_query(user_id, message, context)

            if intent == "sheets_query":
                return await self._handle_sheets_query(user_id, message, context)

            if intent == "view_watchlist":
                return await self._handle_view_watchlist(user_id, db)

            if intent == "add_to_watchlist":
                return await self._handle_add_to_watchlist(user_id, message, db)

            if intent == "view_alerts":
                return await self._handle_view_alerts(user_id, db)

            if intent == "upcoming_earnings":
                return await self._handle_upcoming_earnings()

            if intent == "sec_filing_natural":
                return await self._handle_sec_filing(user_id, message, context)

            if intent == "system_status":
                return await self._handle_system_status()

            if intent == "market_sentiment":
                return await self._handle_market_sentiment(message)

            if intent == "reset_profile":
                return await self._handle_reset_profile(user_id, db)

            if intent == "analyze_document":
                return await self._handle_document_question(user_id, message, context)

            financial_data = await self._retrieve_financial_data(intent, message, context)

            response = await self.response_generator.generate(
                intent=intent,
                user_message=message,
                context=context,
                financial_data=financial_data,
            )

            conv_id = await self.context_manager.save_message(
                user_id=user_id,
                role="user",
                content=message,
                db=db,
                conversation_id=conversation_id,
            )
            await self.context_manager.save_message(
                user_id=user_id,
                role="assistant",
                content=response["response"],
                db=db,
                conversation_id=conv_id,
                metadata={"intent": intent, "model": response.get("model_used")},
                intent=intent,
            )

            try:
                await self.user_profiler.update_from_interaction(
                    user_id=user_id,
                    message=message,
                    response=response["response"],
                    intent=intent,
                    db=db,
                )
            except Exception as e:
                logger.error(f"User profiling failed: {e}")

            duration = time.time() - start_time
            logger.info(f"Message processed in {duration:.2f}s, intent={intent}")

            return {
                "response": self._md_to_html(response["response"]),
                "intent": intent,
                "confidence": confidence,
                "insights": response.get("insights", []),
                "follow_up_questions": response.get("follow_up_questions", []),
                "model_used": response.get("model_used"),
                "tokens_used": response.get("tokens_used", 0),
                "cost_estimate": response.get("cost_estimate", 0),
                "duration": duration,
            }

        except Exception as e:
            logger.error(f"Error in process_message for user {user_id}: {e}", exc_info=True)
            try:
                await db.rollback()
            except Exception:
                pass
            return {
                "response": "I encountered an error processing your request. Please try again.",
                "intent": "error",
                "confidence": 0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

    async def _retrieve_financial_data(self, intent: str, message: str, context: Dict) -> Optional[Dict]:
        data = {}
        symbols = self._extract_symbols(message)

        cache_key = f"fin_data_{intent}_{ '_'.join(symbols[:3])}"
        cached = await cache_service.get(cache_key)
        if cached:
            return cached

        if intent in ["query_stock_price", "research_company", "earnings_analysis"] and symbols:
            for symbol in symbols[:3]:
                stock_data = await self.stock_service.get_stock_data(symbol)
                if stock_data:
                    data[symbol] = stock_data
                company_info = await self.stock_service.get_company_info(symbol)
                if company_info:
                    data[f"{symbol}_info"] = company_info

        if intent == "compare_companies" and len(symbols) >= 2:
            for symbol in symbols[:4]:
                stock_data = await self.stock_service.get_stock_data(symbol)
                if stock_data:
                    data[symbol] = stock_data
                company_info = await self.stock_service.get_company_info(symbol)
                if company_info:
                    data[f"{symbol}_info"] = company_info

        if intent == "market_news":
            news = await self.news_service.get_market_news(limit=5)
            data["market_news"] = news

        if intent == "market_overview":
            market_service = MarketService()
            indices = await market_service.get_market_indices()
            data.update(indices)

        if intent == "earnings_analysis" and symbols:
            for symbol in symbols[:1]:
                earnings = await self.stock_service.get_earnings_data(symbol)
                if earnings:
                    data[f"{symbol}_earnings"] = earnings

        if data:
            await cache_service.set(cache_key, data, ttl=300)

        return data if data else None

    async def _handle_sec_filing(self, user_id: int, message: str, context: Dict) -> Dict[str, Any]:
        symbols = self._extract_symbols(message)
        if not symbols:
            return {
                "response": "Which company's SEC filings would you like me to analyze? Please provide a stock ticker (e.g., AAPL, MSFT).",
                "intent": "sec_filing",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        symbol = symbols[0]
        filings = await sec_edgar_service.search_filings(ticker=symbol, limit=3)

        if not filings:
            return {
                "response": f"I couldn't find recent SEC filings for {symbol}. The company may not have recent filings or there might be a connection issue.",
                "intent": "sec_filing",
                "confidence": 0.8,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        reply = f"<b>Recent SEC Filings for {symbol}:</b>\n\n"
        for f in filings:
            reply += f"• <b>{f['form_type']}</b> ({f.get('file_date', f.get('filing_date', 'N/A'))}): {f['description']}\n"

        reply += "\nWould you like me to analyze any of these filings in detail?"

        return {
            "response": reply,
            "intent": "sec_filing",
            "confidence": 0.9,
            "insights": [f"{len(filings)} recent filings found"],
            "follow_up_questions": get_follow_ups("sec_filing", "has_symbols", symbol=symbol, form_type=filings[0]["form_type"]),
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_set_alert(self, user_id: int, message: str, db: AsyncSession) -> Dict[str, Any]:
        import re

        symbols = self._extract_symbols(message)
        if not symbols:
            return {
                "response": "Which stock would you like to set an alert for? Please provide a ticker (e.g., AAPL, MSFT).",
                "intent": "set_alert",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        symbol = symbols[0]
        message_lower = message.lower()

        price_match = re.search(r'\$?(\d+(?:\.\d{1,2})?)', message)
        target_price = float(price_match.group(1)) if price_match else None

        if "below" in message_lower or "drop" in message_lower or "under" in message_lower:
            alert_type = "price_below"
        elif "above" in message_lower or "hit" in message_lower or "reach" in message_lower or "cross" in message_lower:
            alert_type = "price_above"
        elif "%" in message or "percent" in message or "move" in message:
            alert_type = "percent_change"
        else:
            alert_type = "price_above" if target_price else "percent_change"

        if alert_type == "percent_change" and target_price is None:
            target_match = re.search(r'(\d+(?:\.\d+)?)\s*%', message)
            target_price = float(target_match.group(1)) if target_match else 5.0

        if target_price is None:
            return {
                "response": f"What price or percentage change should I track for {symbol}? For example:\n• \"Alert me when {symbol} hits $200\"\n• \"Notify me if {symbol} drops 5%\"",
                "intent": "set_alert",
                "confidence": 0.8,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        from app.models.user import User
        from app.models.document import Alert
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return {
                "response": "Please start the conversation first by typing /start",
                "intent": "set_alert",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        alert = Alert(
            user_id=user.id,
            symbol=symbol.upper(),
            alert_type=alert_type,
            target_value=target_price,
            message=message,
        )
        db.add(alert)
        await db.commit()

        if alert_type == "price_above":
            desc = f"when {symbol.upper()} reaches ${target_price:.2f}"
        elif alert_type == "price_below":
            desc = f"when {symbol.upper()} drops below ${target_price:.2f}"
        else:
            desc = f"when {symbol.upper()} moves {target_price:.1f}%"

        return {
            "response": f"Alert set! I'll notify you {desc}.\n\nYou can check your alerts anytime with /alerts.",
            "intent": "set_alert",
            "confidence": 0.9,
            "insights": [f"Alert created for {symbol.upper()}"],
            "follow_up_questions": get_follow_ups("set_alert", "success"),
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_daily_briefing(self, user_id: int) -> Dict[str, Any]:
        from app.services.background.briefing_compiler import BriefingCompiler
        compiler = BriefingCompiler()
        briefing = await compiler.generate_briefing(user_id)

        return {
            "response": briefing,
            "intent": "daily_briefing",
            "confidence": 1.0,
            "insights": [],
            "follow_up_questions": get_follow_ups("daily_briefing", "default"),
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_portfolio_analysis(self, user_id: int, context: Dict) -> Dict[str, Any]:
        profile = context.get("user_profile", {})
        watchlist = profile.get("watchlist", [])

        if not watchlist:
            return {
                "response": "Your watchlist is empty. Add some stocks first and I'll analyze your portfolio!",
                "intent": "portfolio_analysis",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": get_follow_ups("portfolio_analysis", "empty"),
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        data = {}
        for symbol in watchlist[:10]:
            stock_data = await self.stock_service.get_stock_data(symbol)
            if stock_data:
                data[symbol] = stock_data

        prompt = f"""Analyze this portfolio and provide insights:

Watchlist: {', '.join(watchlist)}
Stock Data: {json.dumps(data, default=str)[:3000]}

Provide:
1. Portfolio overview
2. Best and worst performers
3. Sector diversification
4. Key risks
5. Suggestions"""

        response = await self.ai_service.generate(
            prompt=prompt,
            system_message="You are a portfolio analyst. Be concise and actionable.",
            temperature=0.5,
        )

        return {
            "response": response["content"] if response["success"] else "Could not analyze portfolio.",
            "intent": "portfolio_analysis",
            "confidence": 0.9,
            "insights": [],
            "follow_up_questions": get_follow_ups("portfolio_analysis", "has_holdings"),
            "model_used": response["model"],
            "tokens_used": response["tokens_used"],
            "cost_estimate": response["cost_estimate"],
            "duration": 0,
        }

    async def _handle_email_query(self, user_id: int, message: str, context: Dict) -> Dict[str, Any]:
        from app.services.integrations.google_service import google_service

        if not await google_service.is_connected(user_id):
            return {
                "response": (
                    "Your Google account isn't connected yet. I can't access your emails.\n\n"
                    "To connect, just say: <b>Connect my Google account</b>\n"
                    "Or skip this and ask me about stocks, market news, or anything else."
                ),
                "intent": "email_query",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        query = ""
        message_lower = message.lower()
        for word in ["from", "about", "regarding", "related to"]:
            if word in message_lower:
                idx = message_lower.index(word)
                query = message[idx + len(word):].strip()
                break

        messages = await google_service.get_gmail_messages(user_id, query=query, limit=10)

        if not messages:
            return {
                "response": f"No emails found{' matching \"' + query + "\"" if query else ""}. Your inbox is clear!",
                "intent": "email_query",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        email_summary = "\n".join([
            f"- <b>{m.get('subject', 'No subject')}</b> from {m.get('from', 'Unknown')} ({m.get('date', '')})"
            for m in messages[:10]
        ])

        prompt = f"""Summarize these emails concisely. Highlight any action items or important financial information.

Emails:
{email_summary}

User question: {message}"""

        response = await self.ai_service.generate(
            prompt=prompt,
            system_message="You are a financial assistant summarizing emails. Be concise and highlight action items.",
            temperature=0.3,
        )

        return {
            "response": response["content"] if response["success"] else f"Found {len(messages)} emails but couldn't summarize them.",
            "intent": "email_query",
            "confidence": 0.9,
            "insights": [f"{len(messages)} emails found"],
            "follow_up_questions": [],
            "model_used": response["model"],
            "tokens_used": response["tokens_used"],
            "cost_estimate": response["cost_estimate"],
            "duration": 0,
        }

    async def _handle_calendar_query(self, user_id: int, message: str, context: Dict) -> Dict[str, Any]:
        from app.services.integrations.google_service import google_service

        if not await google_service.is_connected(user_id):
            return {
                "response": (
                    "Your Google account isn't connected yet. I can't access your calendar.\n\n"
                    "To connect, just say: <b>Connect my Google account</b>\n"
                    "Or ask me about stocks, market news, or anything else."
                ),
                "intent": "calendar_query",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        days = 7
        message_lower = message.lower()
        if "today" in message_lower:
            days = 1
        elif "tomorrow" in message_lower:
            days = 2
        elif "week" in message_lower:
            days = 7
        elif "month" in message_lower:
            days = 30

        events = await google_service.get_calendar_events(user_id, days_ahead=days)

        if not events:
            return {
                "response": f"No meetings found in the next {'day' if days == 1 else f'{days} days'}. Your calendar is clear!",
                "intent": "calendar_query",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        event_list = "\n".join([
            f"- <b>{e.get('summary', 'No title')}</b> at {e.get('start', 'TBD')}"
            for e in events[:15]
        ])

        prompt = f"""Summarize these calendar events concisely. Highlight any financial or important meetings.

Events:
{event_list}

User question: {message}"""

        response = await self.ai_service.generate(
            prompt=prompt,
            system_message="You are a financial assistant summarizing calendar events. Be concise and highlight important meetings.",
            temperature=0.3,
        )

        return {
            "response": response["content"] if response["success"] else f"Found {len(events)} events but couldn't summarize them.",
            "intent": "calendar_query",
            "confidence": 0.9,
            "insights": [f"{len(events)} events found"],
            "follow_up_questions": [],
            "model_used": response["model"],
            "tokens_used": response["tokens_used"],
            "cost_estimate": response["cost_estimate"],
            "duration": 0,
        }

    async def _handle_drive_query(self, user_id: int, message: str, context: Dict) -> Dict[str, Any]:
        from app.services.integrations.google_service import google_service

        if not await google_service.is_connected(user_id):
            return {
                "response": (
                    "Your Google account isn't connected yet. I can't access your Drive files.\n\n"
                    "To connect, just say: <b>Connect my Google account</b>\n"
                    "Or ask me about stocks, market news, or anything else."
                ),
                "intent": "drive_query",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        query = ""
        message_lower = message.lower()
        for word in ["about", "related to", "for", "named"]:
            if word in message_lower:
                idx = message_lower.index(word)
                query = message[idx + len(word):].strip()
                break

        files = await google_service.get_drive_files(user_id, query=query, limit=10)

        if not files:
            return {
                "response": f"No files found{' matching \"' + query + "\"" if query else ""} in your Drive.",
                "intent": "drive_query",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        file_list = "\n".join([
            f"- <b>{f.get('name', 'Unknown')}</b> ({f.get('mime_type', '').split('/')[-1]}) - {f.get('modified', 'N/A')}"
            for f in files[:10]
        ])

        return {
            "response": f"<b>Your Drive Files:</b>\n\n{file_list}\n\nWant me to analyze any of these? Just ask!",
            "intent": "drive_query",
            "confidence": 0.9,
            "insights": [f"{len(files)} files found"],
            "follow_up_questions": [],
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_sheets_query(self, user_id: int, message: str, context: dict) -> dict:
        from app.services.integrations.google_service import google_service

        if not await google_service.is_connected(user_id):
            return {
                "response": (
                    "Your Google account isn't connected yet. I can't access your spreadsheets.\n\n"
                    "To connect, just say: <b>Connect my Google account</b>\n"
                    "Or skip this and ask me about stocks, market news, or anything else."
                ),
                "intent": "sheets_query",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        query = ""
        message_lower = message.lower()
        for word in ["about", "related to", "for", "named"]:
            if word in message_lower:
                idx = message_lower.index(word)
                query = message[idx + len(word):].strip()
                break

        files = await google_service.get_drive_files(user_id, query=query, limit=10)
        sheets = [f for f in files if "spreadsheet" in f.get("mime_type", "").lower() or "sheet" in f.get("mime_type", "").lower()]

        if not sheets:
            return {
                "response": f"No spreadsheets found{' matching \"' + query + "\"" if query else ""} in your Drive.",
                "intent": "sheets_query",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        file_list = "\n".join([
            f"- <b>{f.get('name', 'Unknown')}</b> ({f.get('modified', 'N/A')})"
            for f in sheets[:5]
        ])

        return {
            "response": f"<b>Your Spreadsheets:</b>\n\n{file_list}\n\nTell me which one to analyze!",
            "intent": "sheets_query",
            "confidence": 0.9,
            "insights": [f"{len(sheets)} spreadsheets found"],
            "follow_up_questions": [],
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_view_watchlist(self, user_id: int, db) -> dict:
        from sqlalchemy import select
        from app.models.user import User

        result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return {
                "response": "Could not find your profile. Try /start to begin.",
                "intent": "view_watchlist",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        watchlist = user.watchlist or []

        if not watchlist:
            return {
                "response": "Your watchlist is empty. Just tell me a stock symbol or company name to add something!",
                "intent": "view_watchlist",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": get_follow_ups("view_watchlist", "empty"),
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        lines = [f"  - <b>{symbol}</b>" for symbol in watchlist]

        response = f"<b>Your Watchlist:</b>\n\n" + "\n".join(lines)
        response += f"\n\nTracking <b>{len(watchlist)} stocks</b> helps you spot opportunities and manage risk."
        response += "\n\nWant me to analyze any of these?"

        return {
            "response": response,
            "intent": "view_watchlist",
            "confidence": 1.0,
            "insights": [f"{len(watchlist)} stocks tracked"],
            "follow_up_questions": get_follow_ups("view_watchlist", "has_stocks", first_stock=watchlist[0]),
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_add_to_watchlist(self, user_id: int, message: str, db) -> dict:
        symbols = self._extract_symbols(message)

        if not symbols:
            response = (
                "Sure! Just tell me which stocks to add.\n\n"
                "You can say:\n"
                "• \"Add NVDA to my watchlist\"\n"
                "• \"Track Apple and Tesla\"\n"
                "• \"I want to follow MSFT\"\n\n"
                "Or just type a stock ticker like *GOOGL* and I'll add it!"
            )
            return {
                "response": response,
                "intent": "add_to_watchlist",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": get_follow_ups("add_to_watchlist", "no_symbols"),
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        result = await watchlist_manager.add_to_watchlist(user_id, symbols, db)
        response = await watchlist_manager.format_watchlist_response(result, "add")

        added = result.get("added", [])
        already_exists = result.get("already_exists", [])

        if added:
            follow_ups = get_follow_ups("add_to_watchlist", "success", symbol=added[0])
        else:
            follow_ups = get_follow_ups("add_to_watchlist", "already_exists")

        return {
            "response": response,
            "intent": "add_to_watchlist",
            "confidence": 1.0,
            "insights": [f"Watchlist updated: {result.get('total', 0)} stocks"],
            "follow_up_questions": follow_ups,
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_view_alerts(self, user_id: int, db) -> dict:
        from sqlalchemy import select
        from app.models.user import User
        from app.models.document import Alert

        result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return {
                "response": "Could not find your profile.",
                "intent": "view_alerts",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        alert_result = await db.execute(
            select(Alert).where(Alert.user_id == user.id, Alert.is_active == True)
        )
        alerts = alert_result.scalars().all()

        if not alerts:
            return {
                "response": "You have no active alerts. Tell me a stock and a price condition to set one up!",
                "intent": "view_alerts",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": get_follow_ups("view_alerts", "empty"),
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        lines = []
        for alert in alerts:
            lines.append(f"- <b>{alert.symbol}</b> {alert.alert_type} ${alert.target_value:.2f}")

        response = f"<b>Your Active Alerts:</b>\n\n" + "\n".join(lines)
        response += f"\n\nAlerts help you act fast when conditions are met — no need to watch the screen all day."

        return {
            "response": response,
            "intent": "view_alerts",
            "confidence": 1.0,
            "insights": [f"{len(alerts)} alerts active"],
            "follow_up_questions": get_follow_ups("view_alerts", "has_alerts"),
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_upcoming_earnings(self) -> dict:
        from app.services.financial.earnings_calendar import earnings_calendar
        calendar = await earnings_calendar.get_upcoming_earnings()

        if not calendar:
            return {
                "response": "I couldn't fetch the earnings calendar right now. Try again in a moment!",
                "intent": "upcoming_earnings",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        lines = []
        for item in calendar[:10]:
            lines.append(f"- <b>{item.get('symbol', 'N/A')}</b> - {item.get('date', 'N/A')} ({item.get('time', 'N/A')})")

        response = f"<b>Upcoming Earnings:</b>\n\n" + "\n".join(lines)
        response += "\n\nEarnings reports often cause big price swings. Want me to analyze any of these before they report?"

        return {
            "response": response,
            "intent": "upcoming_earnings",
            "confidence": 1.0,
            "insights": [f"{len(calendar)} upcoming reports"],
            "follow_up_questions": get_follow_ups("upcoming_earnings", "has_data"),
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_system_status(self) -> dict:
        from app.config import settings
        from app.services.financial.market_service import MarketService
        market = MarketService()
        status = await market.get_market_status()
        is_open = status.get("is_open", False)

        return {
            "response": (
                "<b>System Status:</b>\n\n"
                "- Bot: <i>Online</i>\n"
                "- Market data: <i>Active</i>\n"
                f"- Market: <i>{'Open' if is_open else 'Closed'}</i>\n"
                "- AI model: <i>MiMo (OpenCode Zen)</i>\n\n"
                "Everything is running smoothly! "
                + ("Market is open — good time to check prices." if is_open else "Market is closed — next open is Monday 9:30 AM ET.")
            ),
            "intent": "system_status",
            "confidence": 1.0,
            "insights": [],
            "follow_up_questions": get_follow_ups("system_status", "default"),
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_market_sentiment(self, message: str) -> dict:
        news = await self.news_service.get_market_news(limit=5)
        news_text = "\n".join([f"- {n.get('title', '')}" for n in news[:5]]) if news else "No recent news available."

        sentiment_result = await self.ai_service.analyze_sentiment(news_text)
        score = sentiment_result if isinstance(sentiment_result, float) else 0.0

        if score > 0.3:
            mood = "Bullish"
            emoji = "📈"
            explanation = "Positive news flow is driving investor optimism."
        elif score < -0.3:
            mood = "Bearish"
            emoji = "📉"
            explanation = "Negative headlines are weighing on market sentiment."
        else:
            mood = "Neutral"
            emoji = "➡️"
            explanation = "Mixed signals — markets are digesting conflicting information."

        return {
            "response": (
                f"{emoji} <b>Market Sentiment: {mood}</b>\n\n"
                f"Sentiment score: <i>{score:+.2f}</i> (range: -1.0 to +1.0)\n\n"
                f"{explanation}\n\n"
                f"<b>Recent headlines:</b>\n{news_text}\n\n"
                f"Want me to dig deeper into any of these?"
            ),
            "intent": "market_sentiment",
            "confidence": 0.9,
            "insights": [f"Sentiment: {mood} ({score:+.2f})"],
            "follow_up_questions": get_follow_ups("market_sentiment", "default"),
            "model_used": "ai",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_document_question(self, user_id: int, message: str, context: dict) -> dict:
        from app.services.document.processor import DocumentProcessor
        from app.database import async_session_factory
        from app.models.document import Document
        from sqlalchemy import select

        async with async_session_factory() as db:
            result = await db.execute(
                select(Document)
                .where(Document.user_id == user_id)
                .order_by(Document.created_at.desc())
                .limit(1)
            )
            doc = result.scalar_one_or_none()

        if not doc:
            return {
                "response": "I don't see any uploaded documents. Upload a PDF first, then ask me questions about it!",
                "intent": "analyze_document",
                "confidence": 1.0,
                "insights": [],
                "follow_up_questions": [],
                "model_used": "system",
                "tokens_used": 0,
                "cost_estimate": 0,
                "duration": 0,
            }

        processor = DocumentProcessor()
        answer = await processor.answer_question(
            content=doc.content or doc.summary or "",
            question=message,
        )

        return {
            "response": answer,
            "intent": "analyze_document",
            "confidence": 0.9,
            "insights": [],
            "follow_up_questions": get_follow_ups("analyze_document", "has_document"),
            "model_used": "ai",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_reset_profile(self, user_id: int, db) -> dict:
        from app.models.user import User
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.onboarding_step = 0
            user.onboarding_completed = False
            user.role = None
            user.sectors = None
            user.watchlist = None
            user.briefing_time = None
            user.briefing_enabled = False
            await db.commit()

        return {
            "response": (
                "Done! Your profile has been reset.\n\n"
                "Let's set you up again. What best describes your role?\n\n"
                "1. *Investor* - Managing my own portfolio\n"
                "2. *Analyst* - Research & financial analysis\n"
                "3. *Founder/Executive* - Running a business\n"
                "4. *Student* - Learning about finance\n"
                "5. *Enthusiast* - Personal interest in markets"
            ),
            "intent": "reset_profile",
            "confidence": 1.0,
            "insights": [],
            "follow_up_questions": [],
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    def _extract_symbols(self, message: str) -> list:
        import re
        known_symbols = {
            "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL", "alphabet": "GOOGL",
            "amazon": "AMZN", "tesla": "TSLA", "nvidia": "NVDA", "meta": "META",
            "netflix": "NFLX", "amd": "AMD", "intel": "INTC", "salesforce": "CRM",
            "berkshire": "BRK.B", "jpmorgan": "JPM", "goldman": "GS", "visa": "V",
            "mastercard": "MA", "walmart": "WMT", "costco": "COST", "coca": "KO",
            "pepsi": "PEP", "disney": "DIS", "boeing": "BA", "airbus": "EADSY",
        }
        symbols = []
        message_lower = message.lower()
        for name, ticker in known_symbols.items():
            if name in message_lower and ticker not in symbols:
                symbols.append(ticker)
        ticker_pattern = r'\b([A-Z]{1,5})\b'
        for match in re.findall(ticker_pattern, message):
            if match not in symbols and len(match) <= 5:
                symbols.append(match)
        return symbols[:5]

    def _is_ambiguous_query(self, message: str) -> bool:
        """Check if a message is too vague and needs clarification."""
        message_lower = message.lower().strip()
        ambiguous_patterns = [
            r"^(?:tell me about|what about|how about|info on|info about)\s+\w+$",
            r"^(?:analyze|analysis of|review|check)\s+\w+$",
            r"^(?:show me|show|get|find)\s+\w+$",
            r"^(?:apple|google|microsoft|tesla|amazon|nvidia|meta)$",
        ]
        import re
        for pattern in ambiguous_patterns:
            if re.match(pattern, message_lower):
                return True
        return False

    async def _ask_clarifying_question(self, message: str, symbol: str) -> Dict[str, Any]:
        """Ask a clarifying question when the query is too vague."""
        return {
            "response": (
                f"What would you like to know about *{symbol}*?\n\n"
                "I can help with:\n"
                "• Current price and market data\n"
                "• Recent news and analysis\n"
                "• Earnings report and financials\n"
                "• SEC filings\n"
                "• Add to watchlist\n"
                "• Set price alerts\n\n"
                "Just tell me what you're interested in!"
            ),
            "intent": "clarification",
            "confidence": 1.0,
            "insights": [],
            "follow_up_questions": get_follow_ups("clarification", "default", symbol=symbol),
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }

    async def _handle_onboarding(self, user_id: int, message: str, db: AsyncSession) -> Dict[str, Any]:
        from app.models.user import User
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=user_id, onboarding_step=0)
            db.add(user)
            await db.commit()

        step = user.onboarding_step
        if step == 0:
            if message.lower().strip() in ["skip", "later", "no", "next"]:
                user.role = "Other"
                user.onboarding_step = 1
                prompt = PromptTemplates.ONBOARDING_STEP_2
            else:
                valid_roles = ["investor", "analyst", "founder", "ceo", "finance professional", "student", "other"]
                message_lower = message.lower().strip()
                matched_role = None
                for role in valid_roles:
                    if role in message_lower:
                        matched_role = role.title()
                        break
                if not matched_role:
                    prompt = (
                        "Please pick one of these roles (or type 'skip'):\n"
                        "- Investor\n- Analyst\n- Founder/CEO\n- Finance Professional\n- Student\n- Other"
                    )
                    return {
                        "response": prompt,
                        "intent": "onboarding",
                        "confidence": 1.0,
                        "insights": [],
                        "follow_up_questions": [],
                        "model_used": "system",
                        "tokens_used": 0,
                        "cost_estimate": 0,
                        "duration": 0,
                    }
                user.role = matched_role
                user.onboarding_step = 1
                prompt = PromptTemplates.ONBOARDING_STEP_2
        elif step == 1:
            if message.lower().strip() in ["skip", "later", "no", "next"]:
                user.sectors = []
            else:
                user.sectors = [s.strip() for s in message.split(",")]
            user.onboarding_step = 2
            prompt = PromptTemplates.ONBOARDING_STEP_3
        elif step == 2:
            if message.lower().strip() in ["skip", "later", "no", "next"]:
                user.watchlist = []
            else:
                user.watchlist = [s.strip().upper() for s in message.split(",")]
            user.onboarding_step = 3
            prompt = PromptTemplates.ONBOARDING_STEP_4
        elif step == 3:
            if message.lower().strip() in ["skip", "later", "no", "next"]:
                user.notification_preferences = {"insights": []}
            else:
                user.notification_preferences = {"insights": [s.strip() for s in message.split(",")]}
            user.onboarding_step = 4
            prompt = PromptTemplates.ONBOARDING_STEP_5
        elif step == 4:
            if message.lower() != "no briefing":
                import re
                time_str = message.strip().upper()
                try:
                    match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)?', time_str)
                    if match:
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        ampm = match.group(3)
                        if ampm == "PM" and hour < 12:
                            hour += 12
                        elif ampm == "AM" and hour == 12:
                            hour = 0
                        if 0 <= hour <= 23 and 0 <= minute <= 59:
                            user.briefing_time = f"{hour:02d}:{minute:02d}"
                            user.briefing_enabled = True
                            from app.services.background.scheduler import scheduler
                            await scheduler.schedule_user_briefing(user.telegram_id, user.briefing_time)
                        else:
                            user.briefing_enabled = False
                    else:
                        user.briefing_enabled = False
                except (ValueError, IndexError):
                    user.briefing_enabled = False
            else:
                user.briefing_enabled = False
            user.onboarding_step = 5
            prompt = PromptTemplates.ONBOARDING_STEP_GOOGLE
        elif step == 5:
            if message.lower() == "connect":
                from app.services.integrations.google_service import google_service
                auth_url = google_service.get_auth_url(user.telegram_id)
                if auth_url:
                    prompt = f"Please connect your Google account here:\n\n{auth_url}\n\nOnce connected, I'll have access to your Gmail, Calendar, Drive, and Sheets."
                else:
                    prompt = "Google integration is not configured yet. You can connect later by asking me to connect your Google account."
            else:
                prompt = "No problem! You can connect your Google account anytime later."
            user.onboarding_step = 6
            user.onboarding_completed = True
            prompt += "\n\n" + PromptTemplates.ONBOARDING_COMPLETE.format(
                role=user.role,
                sectors=", ".join(user.sectors or []),
                watchlist=", ".join(user.watchlist or []),
                briefing_time=user.briefing_time or "Not set",
            )
        else:
            prompt = "How can I help you today?"

        await db.commit()
        return {
            "response": prompt,
            "intent": "onboarding",
            "confidence": 1.0,
            "insights": [],
            "follow_up_questions": [],
            "model_used": "system",
            "tokens_used": 0,
            "cost_estimate": 0,
            "duration": 0,
        }
