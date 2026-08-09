from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    document_type = Column(String(50), nullable=True)
    file_size = Column(Integer, nullable=True)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    key_insights = Column(JSON, default=list)
    chunk_count = Column(Integer, default=0)
    status = Column(String(20), default="processing")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="documents")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    alert_type = Column(String(50), nullable=False)  # price_above, price_below, percent_change
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    triggered = Column(Boolean, default=False)
    message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    triggered_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="alerts")


class Briefing(Base):
    __tablename__ = "briefings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    content = Column(Text, nullable=False)
    market_summary = Column(Text, nullable=True)
    watchlist_updates = Column(JSON, default=list)
    news_highlights = Column(JSON, default=list)
    sent = Column(Boolean, default=False)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="briefings")
