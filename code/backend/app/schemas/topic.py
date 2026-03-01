"""Topic schemas."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# Request schemas
class CreateTopicRequest(BaseModel):
    """Create topic request."""

    title: str = Field(..., min_length=10, max_length=50)
    description: str = Field(..., min_length=50, max_length=500)
    category: str = Field(...)  # tech, business, culture, academic
    outcome_options: list[str] = Field(..., min_length=2, max_length=10)
    expires_at: datetime

    @field_validator("outcome_options")
    @classmethod
    def validate_outcomes(cls, v: list[str]) -> list[str]:
        """Validate outcome options."""
        if len(v) < 2:
            raise ValueError("At least 2 outcome options required")
        if len(v) > 10:
            raise ValueError("Maximum 10 outcome options allowed")
        # Check for duplicates
        if len(v) != len(set(v)):
            raise ValueError("Outcome options must be unique")
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category."""
        allowed = {"tech", "business", "culture", "academic"}
        if v.lower() not in allowed:
            raise ValueError(f"Category must be one of: {', '.join(allowed)}")
        return v.lower()


class SubmitReviewRequest(BaseModel):
    """Submit topic review request."""

    action: str = Field(...)  # approved, rejected
    reason: str | None = None


# Response schemas
class TopicInfo(BaseModel):
    """Topic information."""

    id: str
    title: str
    description: str
    category: str
    outcome_options: list[str]
    creator_id: str
    status: str
    expires_at: datetime
    participant_count: int
    trade_volume: int
    current_prices: list[float] | None = None
    created_at: datetime


class TopicDetail(TopicInfo):
    """Topic detail with full information."""

    settled_at: datetime | None = None
    settled_outcome: int | None = None
    view_count: int = 0


class TopicListResponse(BaseModel):
    """Paginated topic list response."""

    topics: list[TopicInfo]
    total: int
    page: int
    limit: int


class CreateTopicResponse(BaseModel):
    """Create topic response."""

    topic_id: str
    status: str


class ReviewResponse(BaseModel):
    """Review submission response."""

    topic_id: str
    status: str


class CreatorProfileResponse(BaseModel):
    """Creator profile response."""

    status: str
    topic_count: int
    approved_topic_count: int


class MarketPositionInfo(BaseModel):
    """Market position information."""

    topic_id: str
    topic_title: str
    outcome_index: int
    outcome_option: str
    shares: int
    avg_price: float
    current_value: float | None = None
