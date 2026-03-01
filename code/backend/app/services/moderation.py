"""Content moderation service."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.models.moderation import (
    SensitiveWord,
    ContentReview,
    Violation,
    UserRiskLevel,
    UserAppeal,
    CreatorCreditLevel,
)
from app.models.user import User
from app.services.llm import LLMService


class ModerationService:
    """Content moderation business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm_service = LLMService()

    # ========== Sensitive Word Management ==========

    async def check_sensitive_words(self, text: str, language: str = "vi") -> tuple[bool, list[str]]:
        """
        Check if text contains sensitive words.

        Returns:
            Tuple of (has_sensitive_words, matched_words)
        """
        # Get active sensitive words
        stmt = select(SensitiveWord).where(
            and_(
                SensitiveWord.is_active == True,
                SensitiveWord.language == language,
            )
        )
        result = await self.db.execute(stmt)
        sensitive_words = result.scalars().all()

        matched = []
        text_lower = text.lower()

        for word in sensitive_words:
            if word.match_type == "exact":
                if word.word.lower() in text_lower:
                    matched.append(word.word)
            else:  # fuzzy match - simple implementation
                # Check for character variations
                pattern = self._create_fuzzy_pattern(word.word)
                if pattern and re.search(pattern, text_lower, re.IGNORECASE):
                    matched.append(word.word)

        return len(matched) > 0, matched

    def _create_fuzzy_pattern(self, word: str) -> str | None:
        """Create fuzzy match pattern for word."""
        # Simple implementation - can be enhanced
        if len(word) < 3:
            return None
        # Allow some character skipping
        pattern = ".*".join(re.escape(c) for c in word)
        return pattern

    async def add_sensitive_word(
        self, word: str, category: str, language: str = "vi", match_type: str = "exact"
    ) -> SensitiveWord:
        """Add a sensitive word."""
        # Check if exists
        stmt = select(SensitiveWord).where(SensitiveWord.word == word)
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            existing.category = category
            existing.language = language
            existing.match_type = match_type
            existing.is_active = True
            await self.db.flush()
            return existing

        sensitive_word = SensitiveWord(
            word=word,
            category=category,
            language=language,
            match_type=match_type,
        )
        self.db.add(sensitive_word)
        await self.db.flush()
        return sensitive_word

    async def remove_sensitive_word(self, word_id: str) -> bool:
        """Remove/deactivate a sensitive word."""
        stmt = select(SensitiveWord).where(SensitiveWord.id == word_id)
        result = await self.db.execute(stmt)
        word = result.scalar_one_or_none()

        if not word:
            return False

        word.is_active = False
        await self.db.flush()
        return True

    # ========== Content Review ==========

    async def submit_content_for_review(
        self, content_type: str, content_id: str, content_text: str, user_id: str
    ) -> ContentReview:
        """Submit content for review."""
        # Check sensitive words first
        has_sensitive, matched_words = await self.check_sensitive_words(content_text)

        if has_sensitive:
            # Direct rejection
            review = ContentReview(
                content_type=content_type,
                content_id=content_id,
                user_id=user_id,
                content_text=content_text,
                ai_result="high_risk",
                ai_confidence=1.0,
                ai_notes=f"Contains sensitive words: {', '.join(matched_words)}",
                status="rejected",
                reject_reason="Contains prohibited content",
            )
            self.db.add(review)

            # Record violation
            await self.record_violation(
                user_id=user_id,
                violation_type="sensitive_content",
                severity="light",
                content_type=content_type,
                content_id=content_id,
                evidence={"matched_words": matched_words, "content": content_text[:500]},
            )

            await self.db.flush()
            return review

        # Call LLM for AI review
        try:
            ai_result = await self.llm_service.review_content(content_text)
        except Exception:
            ai_result = {"risk": "low", "confidence": 0.5, "notes": "AI service unavailable"}

        # Determine review path
        if ai_result.get("risk") == "high" or ai_result.get("confidence", 0) < 0.8:
            # Need manual review
            review = ContentReview(
                content_type=content_type,
                content_id=content_id,
                user_id=user_id,
                content_text=content_text,
                ai_result="high_risk",
                ai_confidence=ai_result.get("confidence"),
                ai_notes=ai_result.get("notes"),
                status="manual_review",
            )
        else:
            # Auto-approve
            review = ContentReview(
                content_type=content_type,
                content_id=content_id,
                user_id=user_id,
                content_text=content_text,
                ai_result="low_risk",
                ai_confidence=ai_result.get("confidence"),
                ai_notes=ai_result.get("notes"),
                status="approved",
            )

            # Update creator credit if auto-approved
            await self.update_creator_credit(user_id, approved=True)

        self.db.add(review)
        await self.db.flush()
        return review

    async def get_pending_reviews(
        self, content_type: str | None = None, page: int = 1, limit: int = 20
    ) -> tuple[list[ContentReview], int]:
        """Get pending manual reviews."""
        # Count
        count_stmt = select(func.count()).select_from(ContentReview).where(
            ContentReview.status == "manual_review"
        )
        if content_type:
            count_stmt = count_stmt.where(ContentReview.content_type == content_type)

        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get reviews
        stmt = select(ContentReview).where(ContentReview.status == "manual_review")
        if content_type:
            stmt = stmt.where(ContentReview.content_type == content_type)

        stmt = stmt.order_by(ContentReview.created_at.asc()).offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(stmt)
        reviews = list(result.scalars().all())

        return reviews, total

    async def submit_manual_review(
        self, review_id: str, result: str, reason: str | None, auditor_id: str
    ) -> ContentReview:
        """Submit manual review result."""
        stmt = select(ContentReview).where(ContentReview.id == review_id)
        result_data = await self.db.execute(stmt)
        review = result_data.scalar_one_or_none()

        if not review:
            raise ValueError("Review not found")

        if review.status != "manual_review":
            raise ValueError("Review is not pending manual review")

        review.manual_result = result
        review.reject_reason = reason
        review.auditor_id = auditor_id
        review.status = "approved" if result == "approved" else "rejected"
        review.updated_at = datetime.utcnow()

        # Update creator credit
        if result == "approved":
            await self.update_creator_credit(review.user_id, approved=True)
        else:
            await self.update_creator_credit(review.user_id, approved=False)
            # Record violation for rejected content
            await self.record_violation(
                user_id=review.user_id,
                violation_type="content_rejected",
                severity="light",
                content_type=review.content_type,
                content_id=review.content_id,
                evidence={"reason": reason, "content": review.content_text[:500]},
            )

        await self.db.flush()
        return review

    # ========== Violation Management ==========

    async def record_violation(
        self,
        user_id: str,
        violation_type: str,
        severity: str,
        content_type: str | None = None,
        content_id: str | None = None,
        evidence: dict | None = None,
    ) -> Violation:
        """Record a user violation."""
        violation = Violation(
            user_id=user_id,
            violation_type=violation_type,
            severity=severity,
            content_type=content_type,
            content_id=content_id,
            evidence=evidence,
        )
        self.db.add(violation)

        # Update user risk level
        await self.update_user_risk_level(user_id, violation)

        await self.db.flush()
        return violation

    async def update_user_risk_level(self, user_id: str, violation: Violation | None = None) -> UserRiskLevel:
        """Update user risk level based on violations."""
        # Get or create risk level
        stmt = select(UserRiskLevel).where(UserRiskLevel.user_id == user_id)
        result = await self.db.execute(stmt)
        risk_level = result.scalar_one_or_none()

        if not risk_level:
            risk_level = UserRiskLevel(user_id=user_id, risk_level="low", risk_score=0)
            self.db.add(risk_level)

        # Count violations
        count_stmt = select(func.count()).select_from(Violation).where(Violation.user_id == user_id)
        count_result = await self.db.execute(count_stmt)
        violation_count = count_result.scalar() or 0

        risk_level.violation_count = violation_count
        risk_level.last_violation_at = datetime.utcnow()

        # Calculate risk score and level
        score = min(100, violation_count * 10)

        if score >= 80 or (violation and violation.severity == "critical"):
            risk_level.risk_level = "blacklist"
        elif score >= 60:
            risk_level.risk_level = "high"
        elif score >= 30:
            risk_level.risk_level = "medium"
        else:
            risk_level.risk_level = "low"

        risk_level.risk_score = score

        # Set next downgrade time (30 days without violations)
        risk_level.next_downgrade_at = datetime.utcnow() + timedelta(days=30)

        await self.db.flush()
        return risk_level

    async def execute_penalty(
        self, violation_id: str, penalty_type: str, penalty_duration: int | None, reason: str
    ) -> Violation:
        """Execute penalty for a violation."""
        stmt = select(Violation).where(Violation.id == violation_id)
        result = await self.db.execute(stmt)
        violation = result.scalar_one_or_none()

        if not violation:
            raise ValueError("Violation not found")

        violation.penalty_type = penalty_type
        violation.penalty_duration = penalty_duration
        violation.status = "resolved"
        violation.resolved_at = datetime.utcnow()

        # Update user status based on penalty
        if penalty_type == "ban":
            user_stmt = select(User).where(User.id == violation.user_id)
            user_result = await self.db.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            if user:
                user.status = "banned"

        await self.db.flush()
        return violation

    # ========== Appeal Management ==========

    async def create_appeal(
        self, user_id: str, violation_id: str, reason: str, evidence: list[str] | None = None
    ) -> UserAppeal:
        """Create a user appeal."""
        # Check if violation exists and is appealable
        stmt = select(Violation).where(Violation.id == violation_id)
        result = await self.db.execute(stmt)
        violation = result.scalar_one_or_none()

        if not violation:
            raise ValueError("Violation not found")

        if violation.status == "resolved":
            raise ValueError("Violation already resolved")

        appeal = UserAppeal(
            user_id=user_id,
            violation_id=violation_id,
            reason=reason,
            evidence={"urls": evidence} if evidence else None,
        )
        self.db.add(appeal)

        violation.status = "appealed"
        await self.db.flush()

        return appeal

    async def review_appeal(
        self, appeal_id: str, result: str, notes: str | None, reviewer_id: str
    ) -> UserAppeal:
        """Review an appeal."""
        stmt = select(UserAppeal).where(UserAppeal.id == appeal_id)
        result = await self.db.execute(stmt)
        appeal = result.scalar_one_or_none()

        if not appeal:
            raise ValueError("Appeal not found")

        appeal.status = result
        appeal.reviewer_id = reviewer_id
        appeal.review_notes = notes
        appeal.reviewed_at = datetime.utcnow()

        # Update violation status
        violation_stmt = select(Violation).where(Violation.id == appeal.violation_id)
        violation_result = await self.db.execute(violation_stmt)
        violation = violation_result.scalar_one_or_none()

        if violation:
            if result == "approved":
                # Revert penalty
                violation.status = "resolved"
                # TODO: Revert user status if needed
            else:
                violation.status = "resolved"
                violation.resolved_by = reviewer_id
                violation.resolved_at = datetime.utcnow()

        await self.db.flush()
        return appeal

    # ========== Creator Credit System ==========

    async def update_creator_credit(self, user_id: str, approved: bool) -> CreatorCreditLevel:
        """Update creator credit level."""
        stmt = select(CreatorCreditLevel).where(CreatorCreditLevel.user_id == user_id)
        result = await self.db.execute(stmt)
        credit = result.scalar_one_or_none()

        if not credit:
            credit = CreatorCreditLevel(user_id=user_id)
            self.db.add(credit)

        credit.content_count += 1
        if approved:
            credit.approved_count += 1
        else:
            credit.rejected_count += 1

        # Calculate credit score
        if credit.content_count > 0:
            approval_rate = credit.approved_count / credit.content_count
            credit.credit_score = int(approval_rate * 100)

        # Determine credit level
        if credit.credit_score >= 95:
            credit.credit_level = "S"
        elif credit.credit_score >= 80:
            credit.credit_level = "A"
        elif credit.credit_score >= 60:
            credit.credit_level = "B"
        else:
            credit.credit_level = "C"

        await self.db.flush()
        return credit

    async def get_creator_credit(self, user_id: str) -> CreatorCreditLevel | None:
        """Get creator credit level."""
        stmt = select(CreatorCreditLevel).where(CreatorCreditLevel.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
