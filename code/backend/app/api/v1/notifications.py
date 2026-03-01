"""Notifications API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.core.security import verify_token
from app.services.notification import NotificationService
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


async def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    """Get notification service dependency."""
    return NotificationService(db)


@router.get("/notifications")
async def get_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Get user notifications."""
    notifications, total = await notification_service.get_user_notifications(
        user_id=user_id,
        unread_only=unread_only,
        page=page,
        limit=limit,
    )

    return {
        "notifications": [
            {
                "id": n.id,
                "type": n.notification_type,
                "title": n.title,
                "content": n.content,
                "resource_type": n.resource_type,
                "resource_id": n.resource_id,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None,
            }
            for n in notifications
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("/notifications/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Mark notification as read."""
    success = await notification_service.mark_as_read(notification_id, user_id)
    if success:
        return {"status": "success", "message": "Notification marked as read"}
    raise HTTPException(status_code=404, detail="Notification not found")


@router.post("/notifications/read-all")
async def mark_all_as_read(
    user_id: str = Depends(get_current_user_id),
    notification_service: NotificationService = Depends(get_notification_service),
):
    """Mark all notifications as read."""
    count = await notification_service.mark_all_as_read(user_id)
    return {
        "status": "success",
        "message": f"Marked {count} notifications as read",
        "count": count,
    }
