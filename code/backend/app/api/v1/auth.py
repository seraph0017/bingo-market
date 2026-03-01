"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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
from app.services.auth import AuthService
from app.services.audit import AuditService
from app.services.device import DeviceService
from app.core.database import get_db
from app.core.security import verify_token
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()
security = HTTPBearer()


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Get auth service dependency."""
    return AuthService(db)


def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    """Get audit service dependency."""
    return AuditService(db)


def get_device_service(db: AsyncSession = Depends(get_db)) -> DeviceService:
    """Get device service dependency."""
    return DeviceService(db)


@router.post("/register", response_model=RegisterResponse)
async def register(
    data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new user."""
    try:
        user = await auth_service.register(data)
        return RegisterResponse(
            user_id=user.id,
            status=user.status,
            next_step="identity_verification" if user.status == "unverified" else "complete",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
    device_service: DeviceService = Depends(get_device_service),
):
    """Login user."""
    try:
        user, token, refresh_token = await auth_service.login(data)

        # Log successful login
        await audit_service.log_login(
            user_id=user.id,
            success=True,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Add device record
        await device_service.add_device(
            user_id=user.id,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return TokenResponse(
            token=token,
            refresh_token=refresh_token,
            expires_in=7200,  # 2 hours
        )
    except ValueError as e:
        # Log failed login - try to get user for audit log
        user_id = None
        identifier = data.phone or data.email
        if identifier:
            # Try to get user ID for logging
            try:
                from sqlalchemy import select
                from app.models.user import User
                if data.email:
                    stmt = select(User).where(User.email == data.email)
                else:
                    stmt = select(User).where(User.phone == data.phone)
                result = await auth_service.db.execute(stmt)
                user = result.scalar_one_or_none()
                if user:
                    user_id = user.id
            except Exception:
                pass

        if user_id:
            await audit_service.log_login(
                user_id=user_id,
                success=False,
                ip_address=request.client.host if request.client else None,
                error_message=str(e),
            )

        raise HTTPException(status_code=401, detail=str(e))


@router.post("/verify-identity", response_model=VerifyIdentityResponse)
async def verify_identity(
    data: VerifyIdentityRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Verify user identity (18+ KYC)."""
    try:
        # Extract user ID from token
        from app.core.security import verify_token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = await auth_service.verify_identity(payload["sub"], data)
        return VerifyIdentityResponse(
            status=user.status,
            age=user.age if hasattr(user, "age") else None,
            message="认证成功" if user.status == "verified_18plus" else "认证失败",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me", response_model=UserInfo)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Get current user info."""
    from app.core.security import verify_token

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = await auth_service.get_user(payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserInfo(
        id=user.id,
        phone=user.phone[:7] + "****" if user.phone else None,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        role=user.role,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh access token using refresh token."""
    try:
        new_access_token, new_refresh_token = await auth_service.refresh_token(data.refresh_token)
        return TokenResponse(
            token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=7200,  # 2 hours
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Logout user (invalidate token on client side and log the action)."""
    try:
        payload = verify_token(credentials.credentials)
        if payload:
            # Log logout
            await audit_service.log_logout(
                user_id=payload["sub"],
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
        return {"status": "success", "message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-code")
async def send_code(
    data: SendCodeRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Send verification code to phone."""
    try:
        success = await auth_service.send_verification_code(data.phone)
        if success:
            return {"status": "success", "message": "Code sent"}
        return {"status": "error", "message": "Failed to send code"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login-sms", response_model=TokenResponse)
async def login_sms(
    data: SMSLoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Login with SMS verification code."""
    try:
        user, token, refresh_token = await auth_service.sms_login(
            data.phone, data.verification_code
        )

        # Log login
        await audit_service.log_login(
            user_id=user.id,
            success=True,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return TokenResponse(
            token=token,
            refresh_token=refresh_token,
            expires_in=7200,
        )
    except ValueError as e:
        # Log failed login
        try:
            stmt = select(User).where(User.phone == data.phone)
            result = await auth_service.db.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                await audit_service.log_login(
                    user_id=user.id,
                    success=False,
                    ip_address=request.client.host if request.client else None,
                    error_message=str(e),
                )
        except Exception:
            pass

        raise HTTPException(status_code=401, detail=str(e))


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Change user password (requires login)."""
    try:
        # Extract user ID from token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        success = await auth_service.change_password(
            payload["sub"], data.old_password, data.new_password
        )

        # Log password change
        await audit_service.log_password_change(
            user_id=payload["sub"],
            success=True,
            ip_address=request.client.host if request.client else None,
        )

        return {"status": "success", "message": "Password changed successfully"}
    except ValueError as e:
        # Extract user ID for logging
        payload = verify_token(credentials.credentials) if credentials else None
        user_id = payload["sub"] if payload else None

        if user_id:
            await audit_service.log_password_change(
                user_id=user_id,
                success=False,
                ip_address=request.client.host if request.client else None,
                error_message=str(e),
            )

        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-password")
async def reset_password(
    data: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Reset password via phone or email (after verification code validation)."""
    try:
        # TODO: Verify the verification_code via SMS/email service
        # For now, just validate the code format (6 digits)
        if not data.verification_code or len(data.verification_code) != 6:
            raise HTTPException(status_code=400, detail="Invalid verification code")

        success = await auth_service.reset_password(
            data.phone, data.email, data.new_password
        )
        return {"status": "success", "message": "Password reset successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
