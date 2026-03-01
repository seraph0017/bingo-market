"""Settlement announcements API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.database import get_db
from app.services.settlement_announcement import SettlementAnnouncementService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class AnnouncementResponse(BaseModel):
    """Announcement response."""

    id: str
    settlement_id: str
    topic_id: str
    title: str
    content: str
    winning_outcome_index: int
    winning_outcome_text: str
    total_pool: int
    total_winning_shares: int
    total_participants: int
    total_payout: int
    is_published: bool
    published_at: str | None
    created_at: str | None


async def get_announcement_service(
    db: AsyncSession = Depends(get_db),
) -> SettlementAnnouncementService:
    """Get announcement service dependency."""
    return SettlementAnnouncementService(db)


@router.get("/settlements/announcements", response_model=list[AnnouncementResponse])
async def get_announcements(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    announcement_service: SettlementAnnouncementService = Depends(get_announcement_service),
):
    """Get published settlement announcements."""
    announcements, total = await announcement_service.get_announcements(
        page=page, limit=limit, published_only=True
    )

    return [
        AnnouncementResponse(
            id=a.id,
            settlement_id=a.settlement_id,
            topic_id=a.topic_id,
            title=a.title,
            content=a.content,
            winning_outcome_index=a.winning_outcome_index,
            winning_outcome_text=a.winning_outcome_text,
            total_pool=a.total_pool,
            total_winning_shares=a.total_winning_shares,
            total_participants=a.total_participants,
            total_payout=a.total_payout,
            is_published=a.is_published,
            published_at=a.published_at.isoformat() if a.published_at else None,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in announcements
    ]


@router.get("/settlements/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: str,
    announcement_service: SettlementAnnouncementService = Depends(get_announcement_service),
):
    """Get settlement announcement details."""
    announcement = await announcement_service.get_announcement(announcement_id)

    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return AnnouncementResponse(
        id=announcement.id,
        settlement_id=announcement.settlement_id,
        topic_id=announcement.topic_id,
        title=announcement.title,
        content=announcement.content,
        winning_outcome_index=announcement.winning_outcome_index,
        winning_outcome_text=announcement.winning_outcome_text,
        total_pool=announcement.total_pool,
        total_winning_shares=announcement.total_winning_shares,
        total_participants=announcement.total_participants,
        total_payout=announcement.total_payout,
        is_published=announcement.is_published,
        published_at=announcement.published_at.isoformat() if announcement.published_at else None,
        created_at=announcement.created_at.isoformat() if announcement.created_at else None,
    )
