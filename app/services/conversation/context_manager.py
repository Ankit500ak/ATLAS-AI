from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.services.ai.service import AIService, ai_service
from app.config import settings
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages conversation context with intelligent compression and retrieval.
    Builds optimized context windows for AI processing.
    """

    def __init__(self):
        self.ai_service = ai_service
        self.max_working_memory = settings.max_working_memory
        self.token_budget = settings.token_budget
        self._background_tasks: set = set()

    async def build_context(
        self,
        user_id: int,
        new_message: str,
        db: AsyncSession,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        try:
            user = await self._get_user(user_id, db)
        except Exception as e:
            logger.error(f"Failed to get user for context: {e}")
            user = None
        try:
            working_memory = await self._get_working_memory(conversation_id, db)
        except Exception as e:
            logger.error(f"Failed to get working memory: {e}")
            working_memory = []
        try:
            compressed_history = await self._get_compressed_history(user_id, db)
        except Exception as e:
            logger.error(f"Failed to get compressed history: {e}")
            compressed_history = ""
        financial_context = self._extract_financial_context(working_memory, new_message)

        context = {
            "user_profile": self._build_user_profile(user) if user else {},
            "working_memory": working_memory,
            "compressed_history": compressed_history,
            "financial_context": financial_context,
            "current_query": new_message,
        }

        return self._optimize_context(context)

    async def _get_user(self, user_id: int, db: AsyncSession) -> Optional[User]:
        result = await db.execute(select(User).where(User.telegram_id == user_id))
        return result.scalar_one_or_none()

    async def _get_working_memory(self, conversation_id: Optional[int], db: AsyncSession) -> List[Dict]:
        if not conversation_id:
            return []

        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(self.max_working_memory)
        )
        messages = result.scalars().all()
        messages.reverse()

        return [
            {
                "role": msg.role,
                "content": msg.content,
                "intent": msg.intent,
                "timestamp": msg.created_at.isoformat(),
            }
            for msg in messages
        ]

    async def _get_compressed_history(self, user_id: int, db: AsyncSession) -> str:
        user_result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            return ""

        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user.id)
            .order_by(Conversation.updated_at.desc())
            .limit(10)
        )
        conversations = result.scalars().all()

        if not conversations:
            return ""

        summaries = []
        for conv in conversations:
            if conv.summary:
                summaries.append(conv.summary)
            elif conv.title:
                summaries.append(f"Topic: {conv.title}")

        if not summaries:
            return ""

        combined = "\n".join(summaries[:5])
        if len(combined) > 1000:
            compressed = await self.ai_service.summarize(combined, max_length=200)
            return compressed
        return combined

    def _extract_financial_context(self, working_memory: List[Dict], new_message: str) -> Dict:
        import re
        known_symbols = {
            "apple": "AAPL", "microsoft": "MSFT", "google": "GOOGL", "alphabet": "GOOGL",
            "amazon": "AMZN", "tesla": "TSLA", "nvidia": "NVDA", "meta": "META",
        }

        mentioned = set()
        all_text = new_message.lower()
        for msg in working_memory[-5:]:
            all_text += " " + msg.get("content", "").lower()

        for name, ticker in known_symbols.items():
            if name in all_text:
                mentioned.add(ticker)

        ticker_pattern = r'\b([A-Z]{2,5})\b'
        for match in re.findall(ticker_pattern, " ".join([m.get("content", "") for m in working_memory[-5:]])):
            mentioned.add(match)

        return {
            "mentioned_companies": list(mentioned)[:10],
            "conversation_topics": self._extract_topics(working_memory),
        }

    def _extract_topics(self, working_memory: List[Dict]) -> List[str]:
        topics = set()
        for msg in working_memory:
            intent = msg.get("intent")
            if intent:
                topics.add(intent)
        return list(topics)[:5]

    def _build_user_profile(self, user: User) -> Dict:
        return {
            "role": user.role,
            "sectors": user.sectors or [],
            "watchlist": user.watchlist or [],
            "interests": user.interests or {},
            "response_preferences": user.response_preferences or {},
            "briefing_time": user.briefing_time,
        }

    def _optimize_context(self, context: Dict) -> Dict:
        working_memory = context.get("working_memory", [])
        if len(working_memory) > self.max_working_memory:
            context["working_memory"] = working_memory[-self.max_working_memory:]

        compressed = context.get("compressed_history", "")
        if len(compressed) > 800:
            context["compressed_history"] = compressed[:800]

        return context

    async def save_message(
        self,
        user_id: int,
        role: str,
        content: str,
        db: AsyncSession,
        conversation_id: Optional[int] = None,
        metadata: Optional[Dict] = None,
        intent: Optional[str] = None,
    ) -> int:
        user_result = await db.execute(select(User).where(User.telegram_id == user_id))
        user = user_result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User not found for telegram_id={user_id}")

        if not conversation_id:
            conv = Conversation(user_id=user.id, title=None)
            db.add(conv)
            await db.flush()
            conversation_id = conv.id

        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            intent=intent,
            metadata_=metadata or {},
        )
        db.add(message)

        result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        conv = result.scalar_one_or_none()
        if conv:
            conv.updated_at = message.created_at

        await db.commit()

        task = asyncio.create_task(self._generate_summary_background(conversation_id))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

        return conversation_id

    async def _generate_summary_background(self, conversation_id: int):
        """Generate conversation summary in background to avoid blocking."""
        try:
            await asyncio.sleep(5)
            from app.database import async_session_factory
            async with async_session_factory() as db:
                await self._maybe_generate_summary(conversation_id, db)
        except Exception as e:
            logger.debug(f"Background summary generation failed: {e}")

    async def _maybe_generate_summary(self, conversation_id: int, db: AsyncSession):
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = result.scalar_one_or_none()
        if not conv or conv.summary:
            return

        msg_result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        messages = msg_result.scalars().all()

        if len(messages) < 6:
            return

        conversation_text = "\n".join([
            f"{m.role}: {m.content[:200]}" for m in messages[-10:]
        ])

        prompt = f"""Summarize this financial conversation in 1-2 sentences. Focus on:
- What the user was researching or asking about
- Key companies, stocks, or topics discussed
- Any decisions or actions taken

Conversation:
{conversation_text}

Provide a brief summary:"""

        result = await self.ai_service.generate(
            prompt=prompt,
            system_message="You are a conversation summarizer. Be extremely concise.",
            temperature=0.2,
            max_tokens=150,
        )

        if result["success"] and result["content"]:
            conv.summary = result["content"].strip()
            conv.title = messages[0].content[:80] if messages else None
            await db.commit()

    async def get_conversation_history(self, conversation_id: int, db: AsyncSession, limit: int = 50) -> List[Dict]:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        messages = result.scalars().all()
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "intent": msg.intent,
                "timestamp": msg.created_at.isoformat(),
            }
            for msg in messages
        ]
