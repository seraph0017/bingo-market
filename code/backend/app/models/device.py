"""Login device database model."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4

from app.core.database import Base


class LoginDevice(Base):
    """Login device model for tracking user devices."""

    __tablename__ = "login_devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    # Device info
    device_name: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g., "iPhone 14"
    device_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # mobile, tablet, desktop
    os: Mapped[str | None] = mapped_column(String(50), nullable=True)  # iOS, Android, Windows
    browser: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Chrome, Safari

    # Network info
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Device fingerprint
    device_fingerprint: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Status
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<LoginDevice {self.id} - {self.device_name}>"
