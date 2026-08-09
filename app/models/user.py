from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)

    # Onboarding status
    onboarding_completed = Column(Boolean, default=False)
    onboarding_step = Column(Integer, default=0)

    # User preferences
    role = Column(String(50), nullable=True)
    sectors = Column(JSON, default=list)
    watchlist = Column(JSON, default=list)
    briefing_time = Column(String(5), default="08:00")
    briefing_enabled = Column(Boolean, default=True)
    notification_preferences = Column(JSON, default=dict)

    # Personalization data
    interests = Column(JSON, default=dict)
    response_preferences = Column(JSON, default=dict)
    usage_patterns = Column(JSON, default=dict)

    # Connected integrations
    google_connected = Column(Boolean, default=False)
    google_access_token = Column(String(500), nullable=True)
    google_refresh_token = Column(String(500), nullable=True)

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_active = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    briefings = relationship("Briefing", back_populates="user", cascade="all, delete-orphan")
