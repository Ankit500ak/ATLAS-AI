from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.database import async_session_factory
from app.domain.repositories import (
    UserRepository,
    ConversationRepository,
    DocumentRepository,
    AlertRepository,
)
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.document import Document, Alert
import logging

logger = logging.getLogger(__name__)


class SQLAlchemyUserRepository(UserRepository):
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        async with async_session_factory() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        async with async_session_factory() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user

    async def update(self, user: User) -> User:
        async with async_session_factory() as session:
            await session.merge(user)
            await session.commit()
            return user

    async def get_all_active(self, limit: int = 100) -> List[User]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(User).where(User.onboarding_completed == True).limit(limit)
            )
            return result.scalars().all()


class SQLAlchemyConversationRepository(ConversationRepository):
    async def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        async with async_session_factory() as session:
            result = await session.execute(select(Conversation).where(Conversation.id == conversation_id))
            return result.scalar_one_or_none()

    async def get_user_conversations(self, user_id: int, limit: int = 50) -> List[Conversation]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.updated_at.desc())
                .limit(limit)
            )
            return result.scalars().all()

    async def create(self, conversation: Conversation) -> Conversation:
        async with async_session_factory() as session:
            session.add(conversation)
            await session.commit()
            await session.refresh(conversation)
            return conversation

    async def update(self, conversation: Conversation) -> Conversation:
        async with async_session_factory() as session:
            await session.merge(conversation)
            await session.commit()
            return conversation

    async def get_messages(self, conversation_id: int, limit: int = 50) -> List[Message]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .limit(limit)
            )
            return result.scalars().all()

    async def add_message(self, message: Message) -> Message:
        async with async_session_factory() as session:
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message


class SQLAlchemyDocumentRepository(DocumentRepository):
    async def create(self, document: Document) -> Document:
        async with async_session_factory() as session:
            session.add(document)
            await session.commit()
            await session.refresh(document)
            return document

    async def get_latest_by_user(self, user_id: int) -> Optional[Document]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Document)
                .where(Document.user_id == user_id)
                .order_by(Document.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def get_by_id(self, document_id: int) -> Optional[Document]:
        async with async_session_factory() as session:
            result = await session.execute(select(Document).where(Document.id == document_id))
            return result.scalar_one_or_none()


class SQLAlchemyAlertRepository(AlertRepository):
    async def create(self, alert: Alert) -> Alert:
        async with async_session_factory() as session:
            session.add(alert)
            await session.commit()
            await session.refresh(alert)
            return alert

    async def get_active_by_user(self, user_id: int) -> List[Alert]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Alert)
                .where(Alert.user_id == user_id, Alert.is_active == True)
                .order_by(Alert.created_at.desc())
            )
            return result.scalars().all()

    async def get_all_active(self) -> List[Alert]:
        async with async_session_factory() as session:
            result = await session.execute(
                select(Alert).where(Alert.is_active == True)
            )
            return result.scalars().all()

    async def update(self, alert: Alert) -> Alert:
        async with async_session_factory() as session:
            await session.merge(alert)
            await session.commit()
            return alert

    async def delete(self, alert_id: int) -> bool:
        async with async_session_factory() as session:
            result = await session.execute(select(Alert).where(Alert.id == alert_id))
            alert = result.scalar_one_or_none()
            if alert:
                await session.delete(alert)
                await session.commit()
                return True
            return False