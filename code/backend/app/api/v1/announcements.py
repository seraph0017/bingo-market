"""Announcements API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.database import get_db
from app.core.security import verify_token
from app.services.announcement import AnnouncementService
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()


class AnnouncementCreateRequest(BaseModel):
    """Create announcement request."""

    title: str = Field(..., max_length=200)
    content: str
    summary: str | None = None
    announcement_type: str = "system"
    priority: str = "normal"
    target_audience: str = "all"
    expires_at: datetime | None = None


class AnnouncementResponse(BaseModel):
    """Announcement response."""

    id: str
    title: str
    content: str
    summary: str | None
    announcement_type: str
    priority: str
    target_audience: str
    is_published: bool
    published_at: str | None
    expires_at: str | None
    view_count: int
    created_at: str | None


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current user ID from token."""
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


async def get_announcement_service(db: AsyncSession = Depends(get_db)) -> AnnouncementService:
    """Get announcement service dependency."""
    return AnnouncementService(db)


@router.get("/announcements", response_model=list[AnnouncementResponse])
async def get_announcements(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    announcement_type: str | None = Query(None),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
):
    """Get published announcements."""
    announcements, total = await announcement_service.get_announcements(
        page=page, limit=limit, published_only=True, announcement_type=announcement_type
    )

    return [
        AnnouncementResponse(
            id=a.id,
            title=a.title,
            content=a.content,
            summary=a.summary,
            announcement_type=a.announcement_type,
            priority=a.priority,
            target_audience=a.target_audience,
            is_published=a.is_published,
            published_at=a.published_at.isoformat() if a.published_at else None,
            expires_at=a.expires_at.isoformat() if a.expires_at else None,
            view_count=a.view_count,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in announcements
    ]


@router.get("/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: str,
    announcement_service: AnnouncementService = Depends(get_announcement_service),
):
    """Get announcement details."""
    announcement = await announcement_service.get_announcement(announcement_id)

    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    # Increment view count
    await announcement_service.increment_view_count(announcement_id)

    return AnnouncementResponse(
        id=announcement.id,
        title=announcement.title,
        content=announcement.content,
        summary=announcement.summary,
        announcement_type=announcement.announcement_type,
        priority=announcement.priority,
        target_audience=announcement.target_audience,
        is_published=announcement.is_published,
        published_at=announcement.published_at.isoformat() if announcement.published_at else None,
        expires_at=announcement.expires_at.isoformat() if announcement.expires_at else None,
        view_count=announcement.view_count,
        created_at=announcement.created_at.isoformat() if announcement.created_at else None,
    )


@router.post("/announcements")
async def create_announcement(
    data: AnnouncementCreateRequest,
    user_id: str = Depends(get_current_user_id),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
):
    """Create a new announcement (admin only)."""
    # TODO: Add admin role check
    announcement = await announcement_service.create_announcement(
        title=data.title,
        content=data.content,
        summary=data.summary,
        created_by=user_id,
        announcement_type=data.announcement_type,
        priority=data.priority,
        target_audience=data.target_audience,
        expires_at=data.expires_at,
    )
    return {
        "status": "success",
        "message": "Announcement created",
        "announcement_id": announcement.id,
    }


@router.post("/announcements/{announcement_id}/publish")
async def publish_announcement(
    announcement_id: str,
    user_id: str = Depends(get_current_user_id),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
):
    """Publish an announcement (admin only)."""
    success = await announcement_service.publish_announcement(announcement_id)
    if success:
        return {"status": "success", "message": "Announcement published"}
    raise HTTPException(status_code=404, detail="Announcement not found")


@router.post("/announcements/{announcement_id}/unpublish")
async def unpublish_announcement(
    announcement_id: str,
    user_id: str = Depends(get_current_user_id),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
):
    """Unpublish an announcement (admin only)."""
    success = await announcement_service.unpublish_announcement(announcement_id)
    if success:
        return {"status": "success", "message": "Announcement unpublished"}
    raise HTTPException(status_code=404, detail="Announcement not found")


@router.delete("/announcements/{announcement_id}")
async def delete_announcement(
    announcement_id: str,
    user_id: str = Depends(get_current_user_id),
    announcement_service: AnnouncementService = Depends(get_announcement_service),
):
    """Delete an announcement (admin only)."""
    success = await announcement_service.delete_announcement(announcement_id)
    if success:
        return {"status": "success", "message": "Announcement deleted"}
    raise HTTPException(status_code=404, detail="Announcement not found")
