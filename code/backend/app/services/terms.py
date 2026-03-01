"""User terms service."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.terms import UserTerms


class TermsService:
    """User terms service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_terms(self, language: str = "vi") -> UserTerms | None:
        """Get terms and conditions by language."""
        # Try to get active terms for requested language
        stmt = select(UserTerms).where(
            UserTerms.language == language,
            UserTerms.is_active == True,
        ).order_by(UserTerms.version.desc())
        result = await self.db.execute(stmt)
        terms = result.scalar_one_or_none()

        # Fallback to English if not found
        if not terms and language != "en":
            stmt = select(UserTerms).where(
                UserTerms.language == "en",
                UserTerms.is_active == True,
            ).order_by(UserTerms.version.desc())
            result = await self.db.execute(stmt)
            terms = result.scalar_one_or_none()

        return terms

    async def create_terms(
        self,
        language: str,
        title: str,
        content: str,
        version: str = "1.0.0",
    ) -> UserTerms:
        """Create new terms and conditions."""
        terms = UserTerms(
            language=language,
            title=title,
            content=content,
            version=version,
            is_active=True,
        )
        self.db.add(terms)
        await self.db.flush()
        return terms

    async def deactivate_terms(self, terms_id: str) -> bool:
        """Deactivate terms."""
        stmt = select(UserTerms).where(UserTerms.id == terms_id)
        result = await self.db.execute(stmt)
        terms = result.scalar_one_or_none()

        if not terms:
            return False

        terms.is_active = False
        await self.db.flush()
        return True
