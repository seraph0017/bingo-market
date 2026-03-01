"""Notification database model."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4

from app.core.database import Base


class UserNotification(Base):
    """User notification model."""

    __tablename__ = "user_notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    # Notification type
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)  # settlement, system, trade, etc.

    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Related resource
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # settlement, topic, etc.
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # Extra data
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pushed: Mapped[bool] = mapped_column(Boolean, default=False)  # Sent via WebSocket/push

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<UserNotification {self.id} user={self.user_id} type={self.notification_type}>"
