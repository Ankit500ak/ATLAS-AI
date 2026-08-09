from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class UserCreate(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    onboarding_completed: bool
    role: Optional[str]
    sectors: List[str]
    watchlist: List[str]
    briefing_time: str
    briefing_enabled: bool
    created_at: datetime
    last_active: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    role: Optional[str] = None
    sectors: Optional[List[str]] = None
    watchlist: Optional[List[str]] = None
    briefing_time: Optional[str] = None
    briefing_enabled: Optional[bool] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    interests: Optional[Dict[str, Any]] = None
    response_preferences: Optional[Dict[str, Any]] = None
