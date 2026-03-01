"""Wallet schemas."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# Request schemas
class CreateRechargeOrderRequest(BaseModel):
    """Create recharge order request."""

    amount: int = Field(..., gt=0, description="Recharge amount in VND")
    payment_method: str = Field(..., description="Payment method (momo/zalopay)")

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: int) -> int:
        """Validate amount is at least 10,000 VND and multiple of 1,000."""
        if v < 10_000:
            raise ValueError("Minimum recharge amount is 10,000 VND")
        if v % 1_000 != 0:
            raise ValueError("Amount must be multiple of 1,000 VND")
        return v


# Response schemas
class WalletInfo(BaseModel):
    """Wallet information response."""

    balance: int
    daily_limit_remaining: int
    monthly_limit_remaining: int
    is_verified: bool
    status: str


class RechargeOrderResponse(BaseModel):
    """Recharge order response."""

    order_id: str
    amount_vnd: int
    amount_tokens: int
    payment_method: str
    status: str
    redirect_url: str | None = None
    created_at: datetime


class RechargeRecord(BaseModel):
    """Recharge record response."""

    order_id: str
    amount_vnd: int
    amount_tokens: int
    payment_method: str
    status: str
    created_at: datetime
    paid_at: datetime | None = None


class RechargeRecordsResponse(BaseModel):
    """Paginated recharge records response."""

    records: list[RechargeRecord]
    total: int
    page: int
    limit: int


class TransactionRecord(BaseModel):
    """Wallet transaction record."""

    id: str
    amount: int
    balance_after: int
    transaction_type: str
    description: str | None = None
    created_at: datetime


class TransactionRecordsResponse(BaseModel):
    """Paginated transaction records response."""

    transactions: list[TransactionRecord]
    total: int
    page: int
    limit: int
