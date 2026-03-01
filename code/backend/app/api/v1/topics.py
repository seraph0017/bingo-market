"""Topics API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.topic import (
    TopicInfo,
    TopicDetail,
    TopicListResponse,
    CreateTopicRequest,
    CreateTopicResponse,
    SubmitReviewRequest,
    ReviewResponse,
    CreatorProfileResponse,
)
from app.services.topic import TopicService
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


async def get_topic_service(db: AsyncSession = Depends(get_db)) -> TopicService:
    """Get topic service dependency."""
    return TopicService(db)


@router.get("/", response_model=TopicListResponse)
async def list_topics(
    category: str | None = Query(None),
    sort: str = Query("hot"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    topic_service: TopicService = Depends(get_topic_service),
):
    """List topics with filtering and sorting."""
    try:
        topics, total = await topic_service.get_topics(
            category=category, sort=sort, page=page, limit=limit
        )

        topic_list = [
            TopicInfo(
                id=t.id,
                title=t.title,
                description=t.description,
                category=t.category,
                outcome_options=t.outcome_options,
                creator_id=t.creator_id,
                status=t.status,
                expires_at=t.expires_at,
                participant_count=t.participant_count,
                trade_volume=t.trade_volume,
                created_at=t.created_at,
            )
            for t in topics
        ]

        return TopicListResponse(topics=topic_list, total=total, page=page, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{topic_id}", response_model=TopicDetail)
async def get_topic(
    topic_id: str,
    topic_service: TopicService = Depends(get_topic_service),
):
    """Get topic details."""
    topic = await topic_service.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    # Calculate current prices
    prices = await topic_service.calculate_current_prices(topic)

    return TopicDetail(
        id=topic.id,
        title=topic.title,
        description=topic.description,
        category=topic.category,
        outcome_options=topic.outcome_options,
        creator_id=topic.creator_id,
        status=topic.status,
        expires_at=topic.expires_at,
        settled_at=topic.settled_at,
        settled_outcome=topic.settled_outcome,
        participant_count=topic.participant_count,
        trade_volume=topic.trade_volume,
        view_count=topic.view_count,
        created_at=topic.created_at,
        current_prices=prices,
    )


@router.post("/", response_model=CreateTopicResponse)
async def create_topic(
    data: CreateTopicRequest,
    user_id: str = Depends(get_current_user_id),
    topic_service: TopicService = Depends(get_topic_service),
):
    """Create a new topic (creators only)."""
    try:
        topic = await topic_service.create_topic(user_id, data)
        return CreateTopicResponse(topic_id=topic.id, status=topic.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/creator/profile", response_model=CreatorProfileResponse)
async def get_creator_profile(
    user_id: str = Depends(get_current_user_id),
    topic_service: TopicService = Depends(get_topic_service),
):
    """Get creator profile status."""
    profile = await topic_service.get_creator_profile(user_id)
    if not profile:
        # Create pending profile
        profile = await topic_service.request_creator_profile(user_id)

    return CreatorProfileResponse(
        status=profile.status,
        topic_count=profile.topic_count,
        approved_topic_count=profile.approved_topic_count,
    )


@router.post("/{topic_id}/review", response_model=ReviewResponse)
async def submit_review(
    topic_id: str,
    data: SubmitReviewRequest,
    user_id: str = Depends(get_current_user_id),
    topic_service: TopicService = Depends(get_topic_service),
):
    """Submit topic review (auditors only)."""
    try:
        topic = await topic_service.submit_review(
            topic_id, user_id, data.action, data.reason
        )
        return ReviewResponse(topic_id=topic.id, status=topic.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reviews/pending")
async def get_pending_reviews(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    topic_service: TopicService = Depends(get_topic_service),
):
    """Get pending review topics (auditors only)."""
    # TODO: Add auditor role check
    topics, total = await topic_service.get_pending_reviews(page=page, limit=limit)

    return {
        "topics": [
            {
                "id": t.id,
                "title": t.title,
                "category": t.category,
                "created_at": t.created_at,
            }
            for t in topics
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/search", response_model=TopicListResponse)
async def search_topics(
    q: str = Query(..., min_length=1, description="Search query"),
    category: str | None = Query(None),
    status: str = Query("active"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    topic_service: TopicService = Depends(get_topic_service),
):
    """Search topics by keyword."""
    try:
        topics, total = await topic_service.search_topics(
            query=q, category=category, status=status, page=page, limit=limit
        )

        topic_list = [
            TopicInfo(
                id=t.id,
                title=t.title,
                description=t.description,
                category=t.category,
                outcome_options=t.outcome_options,
                creator_id=t.creator_id,
                status=t.status,
                expires_at=t.expires_at,
                participant_count=t.participant_count,
                trade_volume=t.trade_volume,
                created_at=t.created_at,
            )
            for t in topics
        ]

        return TopicListResponse(topics=topic_list, total=total, page=page, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
