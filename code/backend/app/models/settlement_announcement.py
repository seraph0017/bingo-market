"""Settlement Public Announcement database model."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4

from app.core.database import Base


class SettlementAnnouncement(Base):
    """Public settlement announcement."""

    __tablename__ = "settlement_announcements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    settlement_id: Mapped[str] = mapped_column(String(36), ForeignKey("market_settlements.id"), unique=True)
    topic_id: Mapped[str] = mapped_column(String(36), ForeignKey("topics.id"), index=True)

    # Announcement content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Settlement details
    winning_outcome_index: Mapped[int] = mapped_column(Integer)
    winning_outcome_text: Mapped[str] = mapped_column(String(200), nullable=False)  # Text of winning option
    total_pool: Mapped[int] = mapped_column(BigInteger)
    total_winning_shares: Mapped[int] = mapped_column(BigInteger)

    # Statistics
    total_participants: Mapped[int] = mapped_column(Integer, default=0)
    total_payout: Mapped[int] = mapped_column(BigInteger, default=0)

    # Visibility
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<SettlementAnnouncement {self.id} topic={self.topic_id}>"
