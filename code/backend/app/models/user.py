"""User database models."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4

from app.core.database import Base


class User(Base):
    """User model for authentication and profile."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    # Profile information (set after identity verification)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    id_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    birth_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Status: pending, unverified, verified_18plus, rejected, banned
    status: Mapped[str] = mapped_column(String(20), default="pending")
    role: Mapped[str] = mapped_column(String(20), default="user")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.id}>"
