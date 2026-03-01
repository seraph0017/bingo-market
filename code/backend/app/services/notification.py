"""Notification service."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.notification import UserNotification


class NotificationService:
    """Notification service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_notification(
        self,
        user_id: str,
        notification_type: str,
        title: str,
        content: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        data: Optional[dict] = None,
    ) -> UserNotification:
        """Create a notification for user."""
        notification = UserNotification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            content=content,
            resource_type=resource_type,
            resource_id=resource_id,
            data=data,
        )
        self.db.add(notification)
        await self.db.flush()
        return notification

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[UserNotification], int]:
        """Get user notifications."""
        from sqlalchemy import func, and_

        # Build filters
        filters = [UserNotification.user_id == user_id]
        if unread_only:
            filters.append(UserNotification.is_read == False)

        # Count total
        count_stmt = select(func.count()).select_from(UserNotification).where(and_(*filters))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get notifications
        stmt = (
            select(UserNotification)
            .where(and_(*filters))
            .order_by(desc(UserNotification.created_at))
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        notifications = list(result.scalars().all())

        return notifications, total

    async def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read."""
        stmt = select(UserNotification).where(
            UserNotification.id == notification_id,
            UserNotification.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        notification = result.scalar_one_or_none()

        if not notification:
            return False

        notification.is_read = True
        notification.read_at = datetime.utcnow()
        await self.db.flush()
        return True

    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user."""
        stmt = select(UserNotification).where(
            UserNotification.user_id == user_id,
            UserNotification.is_read == False,
        )
        result = await self.db.execute(stmt)
        notifications = result.scalars().all()

        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            count += 1

        await self.db.flush()
        return count

    async def create_settlement_notification(
        self,
        user_id: str,
        settlement_id: str,
        topic_id: str,
        topic_title: str,
        payout: int,
        winning_outcome_index: int,
    ) -> UserNotification:
        """Create settlement notification."""
        title = "结算结果通知"
        if payout > 0:
            content = f"恭喜！您在话题「{topic_title}」中获得收益 {payout} 知识币"
        else:
            content = f"很遗憾，您在话题「{topic_title}」中未获得收益"

        return await self.create_notification(
            user_id=user_id,
            notification_type="settlement",
            title=title,
            content=content,
            resource_type="settlement",
            resource_id=settlement_id,
            data={
                "topic_id": topic_id,
                "topic_title": topic_title,
                "payout": payout,
                "winning_outcome_index": winning_outcome_index,
            },
        )
