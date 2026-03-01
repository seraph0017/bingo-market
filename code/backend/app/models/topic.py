"""Topic database models."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4

from app.core.database import Base


class Topic(Base):
    """Topic/Prediction market."""

    __tablename__ = "topics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text)

    # Category: tech, business, culture, academic
    category: Mapped[str] = mapped_column(String(50))

    # Outcome options stored as JSON array
    outcome_options: Mapped[dict] = mapped_column(JSONB)

    # Creator
    creator_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    # Status: draft, pending_review, active, expired, settled, rejected, suspended
    status: Mapped[str] = mapped_column(String(20), default="draft")

    # Expiration
    expires_at: Mapped[datetime]
    settled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    settled_outcome: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Index of winning option

    # Stats
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    participant_count: Mapped[int] = mapped_column(Integer, default=0)
    trade_volume: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_topics_status_category", "status", "category"),
        Index("ix_topics_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<Topic {self.id} title='{self.title}' status='{self.status}'>"


class TopicReview(Base):
    """Topic review/audit log."""

    __tablename__ = "topic_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    topic_id: Mapped[str] = mapped_column(String(36), ForeignKey("topics.id"), index=True)
    auditor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))

    # Action: approved, rejected
    action: Mapped[str] = mapped_column(String(20))
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<TopicReview {self.id} topic={self.topic_id} action={self.action}>"


class CreatorProfile(Base):
    """Creator profile/qualification."""

    __tablename__ = "creator_profiles"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)

    # Status: pending, approved, rejected
    status: Mapped[str] = mapped_column(String(20), default="pending")
    approved_by: Mapped[str | None] = mapped_column(String(36), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Stats
    topic_count: Mapped[int] = mapped_column(Integer, default=0)
    approved_topic_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<CreatorProfile {self.user_id} status={self.status}>"


class MarketPosition(Base):
    """User position in a prediction market."""

    __tablename__ = "market_positions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    topic_id: Mapped[str] = mapped_column(String(36), ForeignKey("topics.id"), index=True)

    # Outcome index the user bought
    outcome_index: Mapped[int] = mapped_column(Integer)

    # Number of shares owned
    shares: Mapped[int] = mapped_column(Integer, default=0)

    # Average buy price
    avg_price: Mapped[float] = mapped_column(default=0.0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<MarketPosition {self.id} user={self.user_id} topic={self.topic_id}>"
