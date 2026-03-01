"""Authentication schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


# Request schemas
class RegisterRequest(BaseModel):
    """User registration request."""

    phone: str | None = Field(None, description="Phone number")
    email: EmailStr | None = Field(None, description="Email address")
    password: str = Field(..., min_length=8, max_length=20, description="Password")
    full_name: str | None = Field(None, description="Full name (optional at registration)")
    verification_code: str | None = Field(None, description="SMS verification code (optional)")


class LoginRequest(BaseModel):
    """User login request."""

    phone: str | None = Field(None, description="Phone number")
    email: EmailStr | None = Field(None, description="Email address")
    password: str = Field(..., description="Password")


class VerifyIdentityRequest(BaseModel):
    """Identity verification request (18+ KYC)."""

    full_name: str = Field(..., description="Full name as on ID")
    id_number: str = Field(..., description="National ID number")
    birth_date: str = Field(..., description="Date of birth (YYYY-MM-DD)")


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request."""

    old_password: str = Field(..., min_length=8, max_length=20, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=20, description="New password")


class ResetPasswordRequest(BaseModel):
    """Reset password request (forgot password)."""

    phone: str | None = Field(None, description="Phone number")
    email: EmailStr | None = Field(None, description="Email address")
    new_password: str = Field(..., min_length=8, max_length=20, description="New password")
    verification_code: str = Field(..., description="Verification code from SMS/email")


class SendCodeRequest(BaseModel):
    """Send verification code request."""

    phone: str = Field(..., description="Phone number")


class SMSLoginRequest(BaseModel):
    """SMS login request."""

    phone: str = Field(..., description="Phone number")
    verification_code: str = Field(..., description="Verification code")


# Response schemas
class TokenResponse(BaseModel):
    """Token response."""

    token: str
    refresh_token: str
    expires_in: int


class UserInfo(BaseModel):
    """User information."""

    id: str
    phone: str | None = None
    email: str | None = None
    full_name: str | None = None
    age: int | None = None
    status: str
    role: str
    created_at: str | None = None


class RegisterResponse(BaseModel):
    """Registration response."""

    user_id: str
    status: str
    next_step: str


class VerifyIdentityResponse(BaseModel):
    """Identity verification response."""

    status: str
    age: int | None = None
    message: str | None = None
