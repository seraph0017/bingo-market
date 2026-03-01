"""Pydantic schemas for request/response validation."""

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    VerifyIdentityRequest,
    RegisterResponse,
    TokenResponse,
    VerifyIdentityResponse,
    UserInfo,
)
from app.schemas.wallet import (
    WalletInfo,
    CreateRechargeOrderRequest,
    RechargeOrderResponse,
    RechargeRecordsResponse,
    TransactionRecordsResponse,
)

__all__ = [
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "VerifyIdentityRequest",
    "RegisterResponse",
    "TokenResponse",
    "VerifyIdentityResponse",
    "UserInfo",
    # Wallet
    "WalletInfo",
    "CreateRechargeOrderRequest",
    "RechargeOrderResponse",
    "RechargeRecordsResponse",
    "TransactionRecordsResponse",
]
