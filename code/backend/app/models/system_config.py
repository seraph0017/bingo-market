"""System Configuration database model."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4

from app.core.database import Base


class SystemConfig(Base):
    """System configuration model."""

    __tablename__ = "system_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    config_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string

    # Value type: string, number, boolean, json
    value_type: Mapped[str] = mapped_column(String(20), default="string")

    # Description
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Visibility
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)  # Visible to users
    is_editable: Mapped[bool] = mapped_column(Boolean, default=True)  # Can be edited

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<SystemConfig {self.config_key}>"
