from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.models.user import User
from app.models.conversation import Conversation, Message
from app.models.document import Document, Alert
from datetime import datetime


class UserRepository(ABC):
    @abstractmethod
    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def create(self, user: User) -> User:
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        pass

    @abstractmethod
    async def get_all_active(self, limit: int = 100) -> List[User]:
        pass


class ConversationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, conversation_id: int) -> Optional[Conversation]:
        pass

    @abstractmethod
    async def get_user_conversations(self, user_id: int, limit: int = 50) -> List[Conversation]:
        pass

    @abstractmethod
    async def create(self, conversation: Conversation) -> Conversation:
        pass

    @abstractmethod
    async def update(self, conversation: Conversation) -> Conversation:
        pass

    @abstractmethod
    async def get_messages(self, conversation_id: int, limit: int = 50) -> List[Message]:
        pass

    @abstractmethod
    async def add_message(self, message: Message) -> Message:
        pass


class DocumentRepository(ABC):
    @abstractmethod
    async def create(self, document: Document) -> Document:
        pass

    @abstractmethod
    async def get_latest_by_user(self, user_id: int) -> Optional[Document]:
        pass

    @abstractmethod
    async def get_by_id(self, document_id: int) -> Optional[Document]:
        pass


class AlertRepository(ABC):
    @abstractmethod
    async def create(self, alert: Alert) -> Alert:
        pass

    @abstractmethod
    async def get_active_by_user(self, user_id: int) -> List[Alert]:
        pass

    @abstractmethod
    async def get_all_active(self) -> List[Alert]:
        pass

    @abstractmethod
    async def update(self, alert: Alert) -> Alert:
        pass

    @abstractmethod
    async def delete(self, alert_id: int) -> bool:
        pass