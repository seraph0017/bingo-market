"""Audit log API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime

from app.services.audit import AuditService
from app.core.database import get_db
from app.core.security import verify_token
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current user ID from token."""
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


async def get_current_user_role(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current user role from token."""
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload.get("role", "user")


async def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    """Get audit service dependency."""
    return AuditService(db)


@router.get("/audit-logs")
async def get_audit_logs(
    action: str | None = None,
    resource_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    role: str = Depends(get_current_user_role),
    audit_service: AuditService = Depends(get_audit_service),
):
    """Get audit logs.

    - Regular users can only view their own logs
    - Admin users can view all logs
    """
    try:
        # Regular users can only view their own logs
        query_user_id = user_id
        if role in ["admin", "super_admin"]:
            query_user_id = None  # Admin can view all

        logs, total = await audit_service.get_audit_logs(
            user_id=query_user_id,
            action=action,
            resource_type=resource_type,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit,
        )

        return {
            "logs": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "status": log.status,
                    "error_message": log.error_message,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "limit": limit,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
