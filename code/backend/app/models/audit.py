"""Audit log database model."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4

from app.core.database import Base


class AuditLog(Base):
    """Audit log model for tracking user actions."""

    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # User info
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Browser/device info
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv4 or IPv6

    # Action info
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)  # e.g., LOGIN, LOGOUT, RECHARGE
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g., USER, WALLET, TOPIC
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)  # Affected resource ID

    # Request info
    method: Mapped[str | None] = mapped_column(String(10), nullable=True)  # HTTP method
    endpoint: Mapped[str | None] = mapped_column(String(255), nullable=True)  # API endpoint
    request_body: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON request body (sanitized)
    response_status: Mapped[int | None] = mapped_column(Integer, nullable=True)  # HTTP status code

    # Result
    status: Mapped[str] = mapped_column(String(20), default="success")  # success, failure, error
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Metadata
    metadata_json: Mapped[str | None] = mapped_column(String(2000), nullable=True)  # Additional JSON metadata

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<AuditLog {self.id} - {self.action} by {self.user_id}>"
