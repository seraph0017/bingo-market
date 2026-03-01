"""User terms API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.database import get_db
from app.services.terms import TermsService
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class TermsResponse(BaseModel):
    """Terms response."""

    id: str
    language: str
    title: str
    content: str
    version: str
    is_active: bool


async def get_terms_service(db: AsyncSession = Depends(get_db)) -> TermsService:
    """Get terms service dependency."""
    return TermsService(db)


@router.get("/terms", response_model=TermsResponse)
async def get_terms(
    lang: str = Query("vi", description="Language code (vi, en)"),
    terms_service: TermsService = Depends(get_terms_service),
):
    """Get terms and conditions by language."""
    terms = await terms_service.get_terms(lang)

    if not terms:
        raise HTTPException(status_code=404, detail="Terms not found")

    return TermsResponse(
        id=terms.id,
        language=terms.language,
        title=terms.title,
        content=terms.content,
        version=terms.version,
        is_active=terms.is_active,
    )


@router.get("/terms/versions")
async def get_terms_versions(
    lang: str | None = Query(None, description="Language code filter"),
    terms_service: TermsService = Depends(get_terms_service),
):
    """Get all terms versions."""
    from sqlalchemy import select
    from app.models.terms import UserTerms

    stmt = select(UserTerms).order_by(UserTerms.language, UserTerms.version.desc())
    if lang:
        stmt = stmt.where(UserTerms.language == lang)

    result = await terms_service.db.execute(stmt)
    terms_list = result.scalars().all()

    return {
        "versions": [
            {
                "id": t.id,
                "language": t.language,
                "version": t.version,
                "title": t.title,
                "is_active": t.is_active,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in terms_list
        ]
    }
