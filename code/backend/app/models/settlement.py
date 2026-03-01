"""Settlement database models."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4

from app.core.database import Base


class MarketSettlement(Base):
    """Market settlement record."""

    __tablename__ = "market_settlements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    market_id: Mapped[str] = mapped_column(String(36), ForeignKey("topics.id"), unique=True)

    # Winning outcome index
    winning_outcome_index: Mapped[int] = mapped_column(Integer)

    # Total pool and winning shares
    total_pool: Mapped[int] = mapped_column(BigInteger)  # Total knowledge coins in market
    total_shares_winning: Mapped[int] = mapped_column(BigInteger)  # Shares of winning outcome

    # Status: pending, settling, settled, disputed
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Settlement details
    settled_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    settled_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<MarketSettlement {self.id} market={self.market_id}>"


class UserSettlement(Base):
    """User settlement record."""

    __tablename__ = "user_settlements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    settlement_id: Mapped[str] = mapped_column(String(36), ForeignKey("market_settlements.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    # User's outcome and shares
    outcome_index: Mapped[int] = mapped_column(Integer)
    shares: Mapped[int] = mapped_column(BigInteger)

    # Payout (0 if losing outcome)
    payout: Mapped[int] = mapped_column(BigInteger, default=0)

    # Status: pending, paid, failed
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Timestamps
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<UserSettlement {self.id} user={self.user_id} payout={self.payout}>"


class SettlementDispute(Base):
    """Settlement dispute record."""

    __tablename__ = "settlement_disputes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    settlement_id: Mapped[str] = mapped_column(String(36), ForeignKey("market_settlements.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"))

    # Dispute details
    reason: Mapped[str] = mapped_column(Text)
    evidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Status: pending, resolved, rejected
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Resolution
    resolved_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<SettlementDispute {self.id} settlement={self.settlement_id}>"
