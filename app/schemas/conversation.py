from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class MessageCreate(BaseModel):
    content: str
    role: str = "user"


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    intent: Optional[str]
    entities: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None


class ConversationResponse(BaseModel):
    id: int
    title: Optional[str]
    summary: Optional[str]
    topic: Optional[str]
    is_active: bool
    message_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationContext(BaseModel):
    working_memory: List[Dict[str, Any]]
    compressed_history: str
    user_profile: Dict[str, Any]
    financial_context: Dict[str, Any]
    current_query: str
