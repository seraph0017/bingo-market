"""Wallet database models."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import uuid4

from app.core.database import Base


class UserWallet(Base):
    """User wallet for storing knowledge coins."""

    __tablename__ = "user_wallets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), unique=True, index=True)
    balance: Mapped[int] = mapped_column(BigInteger, default=0)  # In knowledge coins (1:1 with VND)

    # Daily and monthly recharge tracking
    daily_recharged: Mapped[int] = mapped_column(BigInteger, default=0)
    daily_recharged_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    monthly_recharged: Mapped[int] = mapped_column(BigInteger, default=0)
    monthly_recharged_month: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status: active, frozen
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        CheckConstraint("balance >= 0", name="check_balance_non_negative"),
    )

    def __repr__(self) -> str:
        return f"<UserWallet {self.user_id} balance={self.balance}>"


class RechargeOrder(Base):
    """Recharge order for fiat to knowledge coins."""

    __tablename__ = "recharge_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    amount_vnd: Mapped[int] = mapped_column(BigInteger)  # VND amount
    amount_tokens: Mapped[int] = mapped_column(BigInteger)  # Knowledge coins (1:1 with VND)

    # Payment method: momo, zalopay, manual
    payment_method: Mapped[str] = mapped_column(String(50))
    # Status: pending, success, failed, cancelled
    status: Mapped[str] = mapped_column(String(20), default="pending")
    external_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Limit tracking at time of order
    daily_limit_used: Mapped[int] = mapped_column(BigInteger, default=0)
    monthly_limit_used: Mapped[int] = mapped_column(BigInteger, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<RechargeOrder {self.id} user={self.user_id} amount={self.amount_vnd}>"


class WalletTransaction(Base):
    """Wallet transaction log."""

    __tablename__ = "wallet_transactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    wallet_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_wallets.id"), index=True)
    amount: Mapped[int] = mapped_column(BigInteger)  # Positive for income, negative for expense

    # Balance after transaction
    balance_after: Mapped[int] = mapped_column(BigInteger)

    # Transaction type: recharge, prediction_purchase, prediction_sale, settlement, purchase
    transaction_type: Mapped[str] = mapped_column(String(50))

    # Reference to related entity
    reference_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Description
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<WalletTransaction {self.id} wallet={self.wallet_id} amount={self.amount}>"
