"""Content moderation schemas."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


# Request schemas
class SubmitContentRequest(BaseModel):
    """Submit content for review request."""

    content_type: str = Field(..., description="Content type (topic/product/comment)")
    content_id: str = Field(..., description="Content ID")
    content_text: str = Field(..., min_length=1, max_length=1000, description="Content text to review")


class SubmitReviewResultRequest(BaseModel):
    """Submit manual review result request."""

    result: str = Field(..., description="Review result (approved/rejected)")
    reason: str | None = Field(None, description="Rejection reason")


class ExecutePenaltyRequest(BaseModel):
    """Execute penalty request."""

    penalty_type: str = Field(..., description="Penalty type (warning/restriction/ban)")
    penalty_duration: int | None = Field(None, ge=1, description="Penalty duration in days")
    reason: str = Field(..., description="Penalty reason")


class CreateAppealRequest(BaseModel):
    """Create user appeal request."""

    violation_id: str = Field(..., description="Violation ID to appeal")
    reason: str = Field(..., min_length=10, max_length=1000, description="Appeal reason")
    evidence: list[str] | None = Field(None, description="Evidence URLs")


class ReviewAppealRequest(BaseModel):
    """Review appeal request."""

    result: str = Field(..., description="Appeal result (approved/rejected)")
    notes: str | None = Field(None, description="Review notes")


# Response schemas
class ContentReviewResponse(BaseModel):
    """Content review response."""

    review_id: str
    status: str
    estimated_time: str | None = None


class ReviewDetailResponse(BaseModel):
    """Review detail response."""

    id: str
    content_type: str
    content_id: str
    user_id: str
    content_text: str
    ai_result: str | None
    ai_confidence: float | None
    ai_notes: str | None
    manual_result: str | None
    reject_reason: str | None
    auditor_id: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class PendingReviewItem(BaseModel):
    """Pending review item."""

    id: str
    content_type: str
    content_id: str
    user_id: str
    content_text: str
    ai_result: str | None
    ai_confidence: float | None
    created_at: datetime


class ViolationResponse(BaseModel):
    """Violation response."""

    id: str
    user_id: str
    violation_type: str
    severity: str
    penalty_type: str
    penalty_duration: int | None
    status: str
    created_at: datetime


class AppealResponse(BaseModel):
    """Appeal response."""

    appeal_id: str
    status: str
    estimated_time: str | None = None


class UserRiskLevelResponse(BaseModel):
    """User risk level response."""

    user_id: str
    risk_level: str
    risk_score: int
    violation_count: int
    last_violation_at: datetime | None


class CreatorCreditLevelResponse(BaseModel):
    """Creator credit level response."""

    user_id: str
    credit_level: str
    credit_score: int
    content_count: int
    approved_count: int
    rejected_count: int
