"""Content moderation API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.moderation import (
    SubmitContentRequest,
    ContentReviewResponse,
    SubmitReviewResultRequest,
    ExecutePenaltyRequest,
    CreateAppealRequest,
    ReviewAppealRequest,
    ReviewDetailResponse,
    PendingReviewItem,
    ViolationResponse,
    AppealResponse,
    UserRiskLevelResponse,
    CreatorCreditLevelResponse,
)
from app.services.moderation import ModerationService
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


async def get_moderation_service(db: AsyncSession = Depends(get_db)) -> ModerationService:
    """Get moderation service dependency."""
    return ModerationService(db)


# ========== Content Review ==========

@router.post("/content/submit", response_model=ContentReviewResponse)
async def submit_content(
    data: SubmitContentRequest,
    user_id: str = Depends(get_current_user_id),
    moderation_service: ModerationService = Depends(get_moderation_service),
):
    """Submit content for review."""
    try:
        review = await moderation_service.submit_content_for_review(
            content_type=data.content_type,
            content_id=data.content_id,
            content_text=data.content_text,
            user_id=user_id,
        )

        estimated_time = None
        if review.status == "manual_review":
            estimated_time = "24 小时内"
        elif review.status == "rejected":
            estimated_time = None

        return ContentReviewResponse(
            review_id=review.id,
            status=review.status,
            estimated_time=estimated_time,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/reviews/pending")
async def list_pending_reviews(
    content_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    moderation_service: ModerationService = Depends(get_moderation_service),
):
    """List pending manual reviews (auditors only)."""
    # TODO: Add auditor role check
    reviews, total = await moderation_service.get_pending_reviews(
        content_type=content_type,
        page=page,
        limit=limit,
    )

    return {
        "reviews": [
            PendingReviewItem(
                id=r.id,
                content_type=r.content_type,
                content_id=r.content_id,
                user_id=r.user_id,
                content_text=r.content_text[:200],
                ai_result=r.ai_result,
                ai_confidence=r.ai_confidence,
                created_at=r.created_at,
            )
            for r in reviews
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/content/reviews/{review_id}")
async def get_review_detail(
    review_id: str,
    user_id: str = Depends(get_current_user_id),
    moderation_service: ModerationService = Depends(get_moderation_service),
):
    """Get review detail."""
    from sqlalchemy import select
    from app.models.moderation import ContentReview

    stmt = select(ContentReview).where(ContentReview.id == review_id)
    result = await moderation_service.db.execute(stmt)
    review = result.scalar_one_or_none()

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    return ReviewDetailResponse(
        id=review.id,
        content_type=review.content_type,
        content_id=review.content_id,
        user_id=review.user_id,
        content_text=review.content_text,
        ai_result=review.ai_result,
        ai_confidence=review.ai_confidence,
        ai_notes=review.ai_notes,
        manual_result=review.manual_result,
        reject_reason=review.reject_reason,
        auditor_id=review.auditor_id,
        status=review.status,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


@router.post("/content/reviews/{review_id}/submit")
async def submit_review_result(
    review_id: str,
    data: SubmitReviewResultRequest,
    user_id: str = Depends(get_current_user_id),
    moderation_service: ModerationService = Depends(get_moderation_service),
):
    """Submit manual review result (auditors only)."""
    try:
        review = await moderation_service.submit_manual_review(
            review_id=review_id,
            result=data.result,
            reason=data.reason,
            auditor_id=user_id,
        )
        return {"message": "审核成功", "new_status": review.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Violation Management ==========

@router.get("/violations")
async def list_violations(
    user_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user_id: str = Depends(get_current_user_id),
    moderation_service: ModerationService = Depends(get_moderation_service),
):
    """List violations. Users can only see their own violations."""
    from sqlalchemy import select, func
    from app.models.moderation import Violation

    # Permission check - users can only see their own violations
    target_user_id = user_id
    if not target_user_id:
        target_user_id = current_user_id
    elif target_user_id != current_user_id:
        # TODO: Add admin check
        raise HTTPException(status_code=403, detail="Not authorized")

    # Count
    count_stmt = select(func.count()).select_from(Violation).where(
        Violation.user_id == target_user_id
    )
    total_result = await moderation_service.db.execute(count_stmt)
    total = total_result.scalar() or 0

    # Get violations
    stmt = select(Violation).where(Violation.user_id == target_user_id)
    stmt = stmt.order_by(Violation.created_at.desc()).offset((page - 1) * limit).limit(limit)

    result = await moderation_service.db.execute(stmt)
    violations = list(result.scalars().all())

    return {
        "violations": [
            ViolationResponse(
                id=v.id,
                user_id=v.user_id,
                violation_type=v.violation_type,
                severity=v.severity,
                penalty_type=v.penalty_type,
                penalty_duration=v.penalty_duration,
                status=v.status,
                created_at=v.created_at,
            )
            for v in violations
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("/violations/{violation_id}/penalty")
async def execute_penalty(
    violation_id: str,
    data: ExecutePenaltyRequest,
    user_id: str = Depends(get_current_user_id),
    moderation_service: ModerationService = Depends(get_moderation_service),
):
    """Execute penalty for a violation (admins only)."""
    try:
        # TODO: Add admin role check
        violation = await moderation_service.execute_penalty(
            violation_id=violation_id,
            penalty_type=data.penalty_type,
            penalty_duration=data.penalty_duration,
            reason=data.reason,
        )

        penalty_expires_at = None
        if violation.penalty_duration:
            from datetime import timedelta
            penalty_expires_at = (violation.resolved_at + timedelta(days=violation.penalty_duration)).isoformat()

        return {
            "message": "处罚执行成功",
            "penalty_expires_at": penalty_expires_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Appeal Management ==========

@router.post("/appeals", response_model=AppealResponse)
async def create_appeal(
    data: CreateAppealRequest,
    user_id: str = Depends(get_current_user_id),
    moderation_service: ModerationService = Depends(get_moderation_service),
):
    """Create a user appeal."""
    try:
        appeal = await moderation_service.create_appeal(
            user_id=user_id,
            violation_id=data.violation_id,
            reason=data.reason,
            evidence=data.evidence,
        )
        return AppealResponse(
            appeal_id=appeal.id,
            status=appeal.status,
            estimated_time="48 小时内",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/appeals/{appeal_id}/review")
async def review_appeal(
    appeal_id: str,
    data: ReviewAppealRequest,
    user_id: str = Depends(get_current_user_id),
    moderation_service: ModerationService = Depends(get_moderation_service),
):
    """Review an appeal (auditors/admins only)."""
    try:
        appeal = await moderation_service.review_appeal(
            appeal_id=appeal_id,
            result=data.result,
            notes=data.notes,
            reviewer_id=user_id,
        )
        return {"message": "申诉处理成功", "new_status": appeal.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== User Risk & Credit ==========

@router.get("/users/{user_id}/risk-level")
async def get_user_risk_level(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    moderation_service: ModerationService = Depends(get_moderation_service),
):
    """Get user risk level."""
    from sqlalchemy import select
    from app.models.moderation import UserRiskLevel

    # Permission check
    if user_id != current_user_id:
        # TODO: Add admin check
        raise HTTPException(status_code=403, detail="Not authorized")

    stmt = select(UserRiskLevel).where(UserRiskLevel.user_id == user_id)
    result = await moderation_service.db.execute(stmt)
    risk = result.scalar_one_or_none()

    if not risk:
        raise HTTPException(status_code=404, detail="Risk level not found")

    return UserRiskLevelResponse(
        user_id=risk.user_id,
        risk_level=risk.risk_level,
        risk_score=risk.risk_score,
        violation_count=risk.violation_count,
        last_violation_at=risk.last_violation_at,
    )


@router.get("/users/{user_id}/credit-level")
async def get_creator_credit_level(
    user_id: str,
    current_user_id: str = Depends(get_current_user_id),
    moderation_service: ModerationService = Depends(get_moderation_service),
):
    """Get creator credit level."""
    credit = await moderation_service.get_creator_credit(user_id)

    if not credit:
        raise HTTPException(status_code=404, detail="Credit level not found")

    return CreatorCreditLevelResponse(
        user_id=credit.user_id,
        credit_level=credit.credit_level,
        credit_score=credit.credit_score,
        content_count=credit.content_count,
        approved_count=credit.approved_count,
        rejected_count=credit.rejected_count,
    )


# ========== Sensitive Word Management (Admin Only) ==========

@router.post("/sensitive-words")
async def add_sensitive_word(
    word: str = Query(...),
    category: str = Query(...),
    language: str = Query("vi"),
    match_type: str = Query("exact"),
    user_id: str = Depends(get_current_user_id),
    moderation_service: ModerationService = Depends(get_moderation_service),
):
    """Add a sensitive word (admins only)."""
    # TODO: Add admin role check
    try:
        sensitive_word = await moderation_service.add_sensitive_word(
            word=word,
            category=category,
            language=language,
            match_type=match_type,
        )
        return {"id": sensitive_word.id, "word": sensitive_word.word, "category": sensitive_word.category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sensitive-words/{word_id}")
async def remove_sensitive_word(
    word_id: str,
    user_id: str = Depends(get_current_user_id),
    moderation_service: ModerationService = Depends(get_moderation_service),
):
    """Remove a sensitive word (admins only)."""
    # TODO: Add admin role check
    success = await moderation_service.remove_sensitive_word(word_id)
    if not success:
        raise HTTPException(status_code=404, detail="Word not found")
    return {"message": "Word removed"}
