"""Announcement service."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_

from app.models.announcement import Announcement


class AnnouncementService:
    """Announcement service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_announcement(
        self,
        title: str,
        content: str,
        created_by: str,
        announcement_type: str = "system",
        priority: str = "normal",
        target_audience: str = "all",
        summary: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> Announcement:
        """Create a new announcement."""
        announcement = Announcement(
            title=title,
            content=content,
            summary=summary,
            created_by=created_by,
            announcement_type=announcement_type,
            priority=priority,
            target_audience=target_audience,
            expires_at=expires_at,
            is_published=False,
        )
        self.db.add(announcement)
        await self.db.flush()
        return announcement

    async def publish_announcement(self, announcement_id: str) -> bool:
        """Publish an announcement."""
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        result = await self.db.execute(stmt)
        announcement = result.scalar_one_or_none()

        if not announcement:
            return False

        announcement.is_published = True
        announcement.published_at = datetime.utcnow()
        await self.db.flush()
        return True

    async def unpublish_announcement(self, announcement_id: str) -> bool:
        """Unpublish an announcement."""
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        result = await self.db.execute(stmt)
        announcement = result.scalar_one_or_none()

        if not announcement:
            return False

        announcement.is_published = False
        announcement.published_at = None
        await self.db.flush()
        return True

    async def get_announcements(
        self,
        page: int = 1,
        limit: int = 20,
        published_only: bool = True,
        announcement_type: Optional[str] = None,
        target_audience: Optional[str] = None,
    ) -> tuple[list[Announcement], int]:
        """Get announcements."""
        # Build filters
        filters = []
        if published_only:
            filters.append(Announcement.is_published == True)
        if announcement_type:
            filters.append(Announcement.announcement_type == announcement_type)
        if target_audience:
            filters.append(Announcement.target_audience == target_audience)

        # Count total
        count_stmt = select(func.count()).select_from(Announcement)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get announcements
        stmt = select(Announcement)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(desc(Announcement.published_at)).offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(stmt)
        announcements = list(result.scalars().all())

        return announcements, total

    async def get_announcement(self, announcement_id: str) -> Announcement | None:
        """Get announcement by ID."""
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def increment_view_count(self, announcement_id: str) -> bool:
        """Increment view count."""
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        result = await self.db.execute(stmt)
        announcement = result.scalar_one_or_none()

        if not announcement:
            return False

        announcement.view_count += 1
        await self.db.flush()
        return True

    async def delete_announcement(self, announcement_id: str) -> bool:
        """Delete an announcement."""
        stmt = select(Announcement).where(Announcement.id == announcement_id)
        result = await self.db.execute(stmt)
        announcement = result.scalar_one_or_none()

        if not announcement:
            return False

        await self.db.delete(announcement)
        await self.db.flush()
        return True
