"""User Terms database model."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4

from app.core.database import Base


class UserTerms(Base):
    """User terms and conditions model."""

    __tablename__ = "user_terms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # Language version
    language: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # vi, en

    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Version control
    version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<UserTerms {self.language} v{self.version}>"
