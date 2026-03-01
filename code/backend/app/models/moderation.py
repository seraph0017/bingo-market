"""Content moderation database models."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4

from app.core.database import Base


class SensitiveWord(Base):
    """Sensitive word library."""

    __tablename__ = "sensitive_words"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    word: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(50))  # politics, religion, sports, porn, violence, etc.
    language: Mapped[str] = mapped_column(String(10))  # vi, en
    match_type: Mapped[str] = mapped_column(String(20), default="exact")  # exact, fuzzy
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<SensitiveWord {self.word} category={self.category}>"


class ContentReview(Base):
    """Content review record."""

    __tablename__ = "content_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    content_type: Mapped[str] = mapped_column(String(50))  # topic, product, comment
    content_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    content_text: Mapped[str] = mapped_column(Text)

    # AI review result
    ai_result: Mapped[str | None] = mapped_column(String(20))  # high_risk, low_risk, error
    ai_confidence: Mapped[float | None] = mapped_column(default=0.0)
    ai_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Manual review result
    manual_result: Mapped[str | None] = mapped_column(String(20))  # approved, rejected
    reject_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    auditor_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)

    # Status: pending, ai_review, manual_review, approved, rejected
    status: Mapped[str] = mapped_column(String(20), default="pending")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<ContentReview {self.id} content_type={self.content_type} status={self.status}>"


class Violation(Base):
    """User violation record."""

    __tablename__ = "violations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    violation_type: Mapped[str] = mapped_column(String(50))  # sensitive_content, spam, fraud, etc.
    severity: Mapped[str] = mapped_column(String(20))  # light, moderate, severe, critical

    content_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    content_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    penalty_type: Mapped[str] = mapped_column(String(50), default="warning")  # warning, restriction, ban
    penalty_duration: Mapped[int | None] = mapped_column(Integer, nullable=True)  # days

    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, appealed, resolved
    resolved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Violation {self.id} user={self.user_id} severity={self.severity}>"


class UserRiskLevel(Base):
    """User risk level record."""

    __tablename__ = "user_risk_levels"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    risk_level: Mapped[str] = mapped_column(String(20))  # low, medium, high, blacklist
    risk_score: Mapped[int] = mapped_column(default=0)  # 0-100
    violation_count: Mapped[int] = mapped_column(default=0)
    last_violation_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_downgrade_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<UserRiskLevel {self.user_id} level={self.risk_level}>"


class UserAppeal(Base):
    """User appeal record."""

    __tablename__ = "user_appeals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    violation_id: Mapped[str] = mapped_column(String(36), ForeignKey("violations.id"), index=True)
    reason: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, rejected
    reviewer_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<UserAppeal {self.id} user={self.user_id} status={self.status}>"


class CreatorCreditLevel(Base):
    """Creator credit level record."""

    __tablename__ = "creator_credit_levels"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), primary_key=True)
    credit_level: Mapped[str] = mapped_column(String(10), default="B")  # S, A, B, C
    credit_score: Mapped[int] = mapped_column(default=50)  # 0-100
    content_count: Mapped[int] = mapped_column(default=0)
    approved_count: Mapped[int] = mapped_column(default=0)
    rejected_count: Mapped[int] = mapped_column(default=0)
    avg_review_time: Mapped[float | None] = mapped_column(nullable=True)  # hours

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<CreatorCreditLevel {self.user_id} level={self.credit_level}>"
