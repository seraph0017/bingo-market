"""Topic service."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.topic import Topic, TopicReview, CreatorProfile, MarketPosition
from app.models.user import User
from app.schemas.topic import CreateTopicRequest


class TopicService:
    """Topic business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_creator_profile(self, user_id: str) -> CreatorProfile | None:
        """Get creator profile."""
        stmt = select(CreatorProfile).where(CreatorProfile.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def request_creator_profile(self, user_id: str) -> CreatorProfile:
        """Request creator profile."""
        profile = CreatorProfile(user_id=user_id, status="pending")
        self.db.add(profile)
        await self.db.flush()
        return profile

    async def create_topic(self, user_id: str, data: CreateTopicRequest) -> Topic:
        """Create a new topic."""
        # Check creator profile - must be approved creator
        profile = await self.get_creator_profile(user_id)
        if not profile or profile.status != "approved":
            raise ValueError("Must be an approved creator to create topics")

        # Validate expires_at (1 day to 365 days from now)
        now = datetime.now(timezone.utc)
        expires_at = data.expires_at
        # If expires_at is naive, assume it's UTC
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < now + timedelta(days=1):
            raise ValueError("Topic must expire at least 24 hours from now")
        if expires_at > now + timedelta(days=365):
            raise ValueError("Topic cannot expire more than 365 days from now")

        # Convert to naive datetime for database storage (PostgreSQL TIMESTAMP WITHOUT TIME ZONE)
        expires_at_naive = expires_at.replace(tzinfo=None)

        # Create topic (all topics start as pending_review)
        topic = Topic(
            title=data.title,
            description=data.description,
            category=data.category,
            outcome_options=data.outcome_options,
            creator_id=user_id,
            expires_at=expires_at_naive,
            status="pending_review",
        )

        self.db.add(topic)
        await self.db.flush()

        # Create review request
        review = TopicReview(topic_id=topic.id, auditor_id=user_id, action="pending")
        self.db.add(review)

        # Update creator stats
        profile.topic_count += 1
        await self.db.flush()

        return topic

    async def get_topics(
        self,
        category: str | None = None,
        status: str = "active",
        sort: str = "hot",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Topic], int]:
        """Get topics with filtering and sorting."""
        # Build filters
        filters = [Topic.status == status]
        if category:
            filters.append(Topic.category == category)

        # Count total
        count_stmt = select(func.count()).select_from(Topic).where(and_(*filters))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Build order by
        if sort == "hot":
            order_by = (Topic.trade_volume * Topic.participant_count).desc()
        elif sort == "newest":
            order_by = Topic.created_at.desc()
        elif sort == "expiring":
            order_by = Topic.expires_at.asc()
        else:
            order_by = Topic.created_at.desc()

        # Get topics
        stmt = (
            select(Topic)
            .where(and_(*filters))
            .order_by(order_by)
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        topics = result.scalars().all()

        return list(topics), total

    async def search_topics(
        self,
        query: str,
        category: str | None = None,
        status: str = "active",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Topic], int]:
        """Search topics by keyword."""
        # Build filters
        filters = [Topic.status == status]
        if category:
            filters.append(Topic.category == category)

        # Search in title and description
        search_filter = or_(
            Topic.title.ilike(f"%{query}%"),
            Topic.description.ilike(f"%{query}%"),
        )
        filters.append(search_filter)

        # Count total
        count_stmt = select(func.count()).select_from(Topic).where(and_(*filters))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get topics
        stmt = (
            select(Topic)
            .where(and_(*filters))
            .order_by(Topic.trade_volume.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        topics = result.scalars().all()

        return list(topics), total

    async def get_topic(self, topic_id: str) -> Topic | None:
        """Get topic by ID."""
        stmt = select(Topic).where(Topic.id == topic_id)
        result = await self.db.execute(stmt)
        topic = result.scalar_one_or_none()

        # Increment view count
        if topic:
            topic.view_count += 1
            await self.db.flush()

        return topic

    async def submit_review(self, topic_id: str, auditor_id: str, action: str, reason: str | None = None) -> Topic:
        """Submit topic review."""
        # Get topic
        stmt = select(Topic).where(Topic.id == topic_id)
        result = await self.db.execute(stmt)
        topic = result.scalar_one_or_none()

        if not topic:
            raise ValueError("Topic not found")

        if topic.status != "pending_review":
            raise ValueError("Topic is not pending review")

        # Update topic status
        if action == "approved":
            topic.status = "active"
        elif action == "rejected":
            topic.status = "rejected"
        else:
            raise ValueError("Invalid review action")

        # Create review record
        review = TopicReview(
            topic_id=topic_id,
            auditor_id=auditor_id,
            action=action,
            reason=reason,
        )
        self.db.add(review)

        # Update creator stats if approved
        if action == "approved":
            profile_stmt = select(CreatorProfile).where(CreatorProfile.user_id == topic.creator_id)
            profile_result = await self.db.execute(profile_stmt)
            profile = profile_result.scalar_one_or_none()
            if profile:
                profile.approved_topic_count += 1
                profile.status = "approved"  # Auto-approve creator after first approved topic

        await self.db.flush()
        return topic

    async def get_pending_reviews(
        self, page: int = 1, limit: int = 20
    ) -> tuple[list[Topic], int]:
        """Get pending review topics."""
        # Count total
        count_stmt = select(func.count()).select_from(Topic).where(
            Topic.status == "pending_review"
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get topics
        stmt = (
            select(Topic)
            .where(Topic.status == "pending_review")
            .order_by(Topic.created_at.asc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        topics = result.scalars().all()

        return list(topics), total

    async def get_user_positions(self, user_id: str) -> list[MarketPosition]:
        """Get user's market positions."""
        stmt = select(MarketPosition).where(MarketPosition.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def calculate_current_prices(self, topic: Topic) -> list[float]:
        """Calculate current prices using LMSR formula."""
        # This will be implemented with the LMSR engine
        # For now, return equal probabilities
        num_outcomes = len(topic.outcome_options)
        return [1.0 / num_outcomes] * num_outcomes
