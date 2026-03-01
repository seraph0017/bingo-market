"""Settlement announcement service."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.settlement_announcement import SettlementAnnouncement
from app.models.settlement import MarketSettlement
from app.models.topic import Topic


class SettlementAnnouncementService:
    """Settlement announcement service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_announcement(
        self,
        settlement_id: str,
        topic_id: str,
        title: str,
        content: str,
        winning_outcome_index: int,
        winning_outcome_text: str,
        total_pool: int,
        total_winning_shares: int,
        total_participants: int,
        total_payout: int,
    ) -> SettlementAnnouncement:
        """Create settlement announcement."""
        announcement = SettlementAnnouncement(
            settlement_id=settlement_id,
            topic_id=topic_id,
            title=title,
            content=content,
            winning_outcome_index=winning_outcome_index,
            winning_outcome_text=winning_outcome_text,
            total_pool=total_pool,
            total_winning_shares=total_winning_shares,
            total_participants=total_participants,
            total_payout=total_payout,
            is_published=False,
        )
        self.db.add(announcement)
        await self.db.flush()
        return announcement

    async def publish_announcement(self, announcement_id: str) -> bool:
        """Publish announcement."""
        stmt = select(SettlementAnnouncement).where(
            SettlementAnnouncement.id == announcement_id
        )
        result = await self.db.execute(stmt)
        announcement = result.scalar_one_or_none()

        if not announcement:
            return False

        announcement.is_published = True
        announcement.published_at = datetime.utcnow()
        await self.db.flush()
        return True

    async def get_announcements(
        self,
        page: int = 1,
        limit: int = 20,
        published_only: bool = True,
    ) -> tuple[list[SettlementAnnouncement], int]:
        """Get settlement announcements."""
        from sqlalchemy import func

        # Build filters
        filters = []
        if published_only:
            filters.append(SettlementAnnouncement.is_published == True)

        # Count total
        count_stmt = select(func.count()).select_from(SettlementAnnouncement)
        if filters:
            from sqlalchemy import and_
            count_stmt = count_stmt.where(and_(*filters))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get announcements
        stmt = select(SettlementAnnouncement)
        if filters:
            from sqlalchemy import and_
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(desc(SettlementAnnouncement.published_at)).offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(stmt)
        announcements = list(result.scalars().all())

        return announcements, total

    async def get_announcement(self, announcement_id: str) -> SettlementAnnouncement | None:
        """Get announcement by ID."""
        stmt = select(SettlementAnnouncement).where(
            SettlementAnnouncement.id == announcement_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_announcement_by_topic(self, topic_id: str) -> SettlementAnnouncement | None:
        """Get announcement by topic ID."""
        stmt = select(SettlementAnnouncement).where(
            SettlementAnnouncement.topic_id == topic_id
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
