"""Authentication service."""

from __future__ import annotations

from datetime import datetime
from typing import TypeAlias
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.schemas.auth import RegisterRequest, LoginRequest, VerifyIdentityRequest
from app.core.config import settings
from app.services.sms import sms_service


UserResult: TypeAlias = tuple[User, str, str]


class AuthService:
    """Authentication business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user."""
        # Validate identifier
        if not data.phone and not data.email:
            raise ValueError("Phone or email is required")

        # Build query based on which identifier is provided
        if data.email:
            stmt = select(User).where(User.email == data.email)
        else:
            stmt = select(User).where(User.phone == data.phone)

        result = await self.db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise ValueError("User already exists")

        # Create user
        user = User(
            phone=data.phone,
            email=data.email,
            full_name=data.full_name,
            password_hash=get_password_hash(data.password),
            status="unverified",
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def login(self, data: LoginRequest) -> UserResult:
        """Login user and return tokens."""
        # Validate identifier
        if not data.phone and not data.email:
            raise ValueError("Phone or email is required")

        # Build query based on which identifier is provided
        if data.email:
            stmt = select(User).where(User.email == data.email)
            identifier = data.email
        else:
            stmt = select(User).where(User.phone == data.phone)
            identifier = data.phone

        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Record failed attempt
            await self._record_failed_attempt(identifier)
            raise ValueError("Invalid credentials")

        # Check if account is locked
        if await self._is_account_locked(identifier):
            raise ValueError(
                f"Account locked due to too many failed attempts. "
                f"Please try again in {settings.login_lockout_duration_minutes} minutes."
            )

        if not verify_password(data.password, user.password_hash):
            # Record failed attempt
            await self._record_failed_attempt(identifier)
            raise ValueError("Invalid credentials")

        if user.status == "banned":
            raise ValueError("Account is banned")

        # Clear failed attempts on successful login
        await self._clear_failed_attempts(identifier)

        # Update last login
        user.last_login_at = datetime.utcnow()
        user.status = user.status if user.status != "pending" else "unverified"
        await self.db.flush()

        # Generate tokens
        token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return user, token, refresh_token

    async def _get_failed_attempts_key(self, identifier: str) -> str:
        """Get Redis key for failed attempts."""
        return f"login_failed:{identifier}"

    async def _get_lock_key(self, identifier: str) -> str:
        """Get Redis key for account lock."""
        return f"login_locked:{identifier}"

    async def _record_failed_attempt(self, identifier: str) -> None:
        """Record a failed login attempt."""
        try:
            from app.core.redis import get_redis
            r = await get_redis()

            key = await self._get_failed_attempts_key(identifier)
            attempts = await r.incr(key)

            # Set expiry on first attempt
            if attempts == 1:
                await r.expire(key, settings.login_lockout_duration_minutes * 60)

            # Lock account if max attempts reached
            if attempts >= settings.login_max_attempts:
                await self._lock_account(identifier)
        except Exception:
            # Redis not available - skip rate limiting
            pass

    async def _lock_account(self, identifier: str) -> None:
        """Lock account after too many failed attempts."""
        try:
            from app.core.redis import get_redis
            r = await get_redis()

            lock_key = await self._get_lock_key(identifier)
            await r.set(lock_key, "1", ex=settings.login_lockout_duration_minutes * 60)
        except Exception:
            pass

    async def _is_account_locked(self, identifier: str) -> bool:
        """Check if account is locked."""
        try:
            from app.core.redis import get_redis
            r = await get_redis()

            lock_key = await self._get_lock_key(identifier)
            return await r.exists(lock_key) > 0
        except Exception:
            return False

    async def _clear_failed_attempts(self, identifier: str) -> None:
        """Clear failed login attempts on successful login."""
        try:
            from app.core.redis import get_redis
            r = await get_redis()

            await r.delete(
                await self._get_failed_attempts_key(identifier),
                await self._get_lock_key(identifier),
            )
        except Exception:
            pass

    async def verify_identity(self, user_id: str, data: VerifyIdentityRequest) -> User:
        """Verify user identity (18+ KYC)."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        if user.status == "verified_18plus":
            raise ValueError("Already verified")

        # Check retry limit (3 times per day)
        from app.core.redis import get_redis
        try:
            redis_client = await get_redis()
            key = f"kyc_retry:{user_id}"
            attempts = await redis_client.get(key)
            if attempts and int(attempts) >= 3:
                raise ValueError("Daily verification limit reached (3 attempts)")
        except Exception:
            pass  # Redis not available, skip limit

        # TODO: Call official ID verification service
        # For now, just parse birth date and calculate age
        from datetime import date
        birth = datetime.strptime(data.birth_date, "%Y-%m-%d").date()
        today = date.today()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

        if age < 18:
            # Increment retry count
            try:
                redis_client = await get_redis()
                key = f"kyc_retry:{user_id}"
                await redis_client.incr(key)
                await redis_client.expire(key, 86400)  # 24 hours
            except Exception:
                pass

            user.status = "rejected"
            await self.db.flush()
            raise ValueError("Must be 18+ to use this platform")

        # Update user with verified info
        user.full_name = data.full_name
        user.id_number = data.id_number  # TODO: Encrypt this
        user.birth_date = birth
        user.status = "verified_18plus"

        # Clear retry count on success
        try:
            redis_client = await get_redis()
            key = f"kyc_retry:{user_id}"
            await redis_client.delete(key)
        except Exception:
            pass

        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def get_user(self, user_id: str) -> User | None:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def refresh_token(self, refresh_token: str) -> tuple[str, str]:
        """Refresh access token using refresh token.

        Returns:
            tuple[str, str]: New access token and refresh token
        """
        payload = verify_refresh_token(refresh_token)
        if not payload:
            raise ValueError("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("Invalid refresh token payload")

        # Verify user still exists
        user = await self.get_user(user_id)
        if not user:
            raise ValueError("User not found")

        if user.status == "banned":
            raise ValueError("Account is banned")

        # Generate new tokens
        new_access_token = create_access_token(user_id)
        new_refresh_token = create_refresh_token(user_id)

        return new_access_token, new_refresh_token

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Verify old password
        if not verify_password(old_password, user.password_hash):
            raise ValueError("Invalid current password")

        # Update password
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        await self.db.flush()

        return True

    async def reset_password(self, phone: str | None, email: str | None, new_password: str) -> bool:
        """Reset password via phone or email (after verification code validated)."""
        if not phone and not email:
            raise ValueError("Phone or email is required")

        # Build query
        if email:
            stmt = select(User).where(User.email == email)
        else:
            stmt = select(User).where(User.phone == phone)

        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError("User not found")

        # Update password
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        await self.db.flush()

        return True

    async def send_verification_code(self, phone: str) -> bool:
        """Send verification code to phone."""
        # Check rate limit
        allowed = await sms_service.check_rate_limit(phone)
        if not allowed:
            raise ValueError("Too many requests. Please try again later.")

        # Generate and send code
        success = await sms_service.send_verification_code(phone)
        return success

    async def sms_login(self, phone: str, code: str) -> tuple[User, str, str]:
        """Login user with SMS verification code."""
        # Verify code
        valid = await sms_service.verify_code(phone, code)
        if not valid:
            raise ValueError("Invalid verification code")

        # Find or create user
        stmt = select(User).where(User.phone == phone)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            # Create new user
            user = User(
                phone=phone,
                password_hash=get_password_hash(str(uuid4())),  # Random password
                status="unverified",
            )
            self.db.add(user)
            await self.db.flush()

        if user.status == "banned":
            raise ValueError("Account is banned")

        # Update last login
        user.last_login_at = datetime.utcnow()
        await self.db.flush()

        # Generate tokens
        token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        return user, token, refresh_token
