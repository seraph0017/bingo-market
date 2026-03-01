"""Announcement database model."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Integer, ForeignKey, Text, DateTime as DateTimeType
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4

from app.core.database import Base


class Announcement(Base):
    """System announcement model."""

    __tablename__ = "announcements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Short summary

    # Type: system, maintenance, update, event
    announcement_type: Mapped[str] = mapped_column(String(50), default="system")

    # Priority: low, normal, high, urgent
    priority: Mapped[str] = mapped_column(String(20), default="normal")

    # Visibility
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Target audience: all, users, admins, creators
    target_audience: Mapped[str] = mapped_column(String(20), default="all")

    # Extra data
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Stats
    view_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Announcement {self.id} title='{self.title}'>"
