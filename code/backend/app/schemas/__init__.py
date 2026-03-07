"""Pydantic schemas for request/response validation."""

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    VerifyIdentityRequest,
    RegisterResponse,
    TokenResponse,
    VerifyIdentityResponse,
    UserInfo,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ResetPasswordRequest,
    SendCodeRequest,
    SMSLoginRequest,
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
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "ResetPasswordRequest",
    "SendCodeRequest",
    "SMSLoginRequest",
    # Wallet
    "WalletInfo",
    "CreateRechargeOrderRequest",
    "RechargeOrderResponse",
    "RechargeRecordsResponse",
    "TransactionRecordsResponse",
]
