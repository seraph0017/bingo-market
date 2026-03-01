"""Settlement service."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.topic import Topic
from app.models.settlement import MarketSettlement, UserSettlement, SettlementDispute
from app.models.wallet import UserWallet
from app.services.wallet import WalletService
from app.services.notification import NotificationService


class SettlementService:
    """Settlement business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_service = WalletService(db)
        self.notification_service = NotificationService(db)

    async def get_expired_topics(self) -> list[Topic]:
        """Get topics that have expired but not yet settled."""
        now = datetime.utcnow()
        stmt = select(Topic).where(
            and_(
                Topic.status == "active",
                Topic.expires_at <= now,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_settlement(self, topic: Topic) -> MarketSettlement:
        """Create settlement record for a topic."""
        # Calculate total pool (total trade volume)
        total_pool = topic.trade_volume

        # Get total shares for each outcome
        from app.models.topic import MarketPosition
        stmt = select(
            MarketPosition.outcome_index,
            func.sum(MarketPosition.shares).label("total_shares"),
        ).where(
            MarketPosition.topic_id == topic.id
        ).group_by(MarketPosition.outcome_index)

        result = await self.db.execute(stmt)
        shares_by_outcome = {row.outcome_index: row.total_shares for row in result.all()}

        # Get total winning shares (will be calculated after result is submitted)
        total_shares_winning = 0

        settlement = MarketSettlement(
            market_id=topic.id,
            winning_outcome_index=-1,  # Not yet determined
            total_pool=total_pool,
            total_shares_winning=total_shares_winning,
            status="pending",
        )

        self.db.add(settlement)
        await self.db.flush()

        return settlement

    async def submit_result(self, settlement_id: str, winning_index: int, submitted_by: str) -> MarketSettlement:
        """Submit settlement result (winning outcome)."""
        stmt = select(MarketSettlement).where(MarketSettlement.id == settlement_id)
        result = await self.db.execute(stmt)
        settlement = result.scalar_one_or_none()

        if not settlement:
            raise ValueError("Settlement not found")

        if settlement.status != "pending":
            raise ValueError("Settlement result already submitted")

        # Validate winning index
        topic_stmt = select(Topic).where(Topic.id == settlement.market_id)
        topic_result = await self.db.execute(topic_stmt)
        topic = topic_result.scalar_one_or_none()

        if not topic:
            raise ValueError("Topic not found")

        if winning_index < 0 or winning_index >= len(topic.outcome_options):
            raise ValueError("Invalid winning outcome index")

        # Update settlement
        settlement.winning_outcome_index = winning_index
        settlement.status = "settling"
        settlement.settled_by = submitted_by

        await self.db.flush()

        return settlement

    async def calculate_payouts(self, settlement: MarketSettlement) -> list[UserSettlement]:
        """Calculate payouts for all users."""
        from app.models.topic import MarketPosition, Topic

        # Get topic
        topic_stmt = select(Topic).where(Topic.id == settlement.market_id)
        topic_result = await self.db.execute(topic_stmt)
        topic = topic_result.scalar_one_or_none()

        if not topic:
            raise ValueError("Topic not found")

        winning_index = settlement.winning_outcome_index

        # Get total winning shares
        from sqlalchemy import select, func
        stmt = select(func.sum(MarketPosition.shares)).where(
            MarketPosition.topic_id == settlement.market_id,
            MarketPosition.outcome_index == winning_index,
        )
        result = await self.db.execute(stmt)
        total_winning_shares = result.scalar() or 0

        settlement.total_shares_winning = total_winning_shares

        # Get all positions
        positions_stmt = select(MarketPosition).where(MarketPosition.topic_id == settlement.market_id)
        positions_result = await self.db.execute(positions_stmt)
        positions = positions_result.scalars().all()

        user_settlements = []

        for position in positions:
            if position.outcome_index == winning_index:
                # Winning outcome: payout = (shares / total_winning_shares) * total_pool
                if total_winning_shares > 0:
                    payout = int((position.shares / total_winning_shares) * settlement.total_pool)
                else:
                    payout = 0
            else:
                # Losing outcome: payout = 0
                payout = 0

            user_settlement = UserSettlement(
                settlement_id=settlement.id,
                user_id=position.user_id,
                outcome_index=position.outcome_index,
                shares=position.shares,
                payout=payout,
                status="pending",
            )
            user_settlements.append(user_settlement)
            self.db.add(user_settlement)

        await self.db.flush()

        return user_settlements

    async def execute_payouts(self, settlement: MarketSettlement) -> int:
        """Execute payouts to all users."""
        stmt = select(UserSettlement).where(
            UserSettlement.settlement_id == settlement.id,
            UserSettlement.status == "pending",
        )
        result = await self.db.execute(stmt)
        user_settlements = result.scalars().all()

        paid_count = 0

        for user_settlement in user_settlements:
            if user_settlement.payout > 0:
                # Credit user wallet
                success = await self.wallet_service.credit_balance(
                    user_id=user_settlement.user_id,
                    amount=user_settlement.payout,
                    transaction_type="settlement",
                    reference_id=settlement.market_id,
                    description=f"Settlement payout for market {settlement.market_id}",
                )

                if success:
                    user_settlement.status = "paid"
                    user_settlement.paid_at = datetime.utcnow()
                    paid_count += 1
                else:
                    user_settlement.status = "failed"
            else:
                # No payout, mark as paid
                user_settlement.status = "paid"
                paid_count += 1

        # Update settlement status
        settlement.status = "settled"
        settlement.settled_at = datetime.utcnow()

        # Update topic status
        topic_stmt = select(Topic).where(Topic.id == settlement.market_id)
        topic_result = await self.db.execute(topic_stmt)
        topic = topic_result.scalar_one_or_none()

        if topic:
            topic.status = "settled"
            topic.settled_outcome = settlement.winning_outcome_index
            topic.settled_at = datetime.utcnow()

        # Send notifications to all users
        for user_settlement in user_settlements:
            try:
                await self.notification_service.create_settlement_notification(
                    user_id=user_settlement.user_id,
                    settlement_id=settlement.id,
                    topic_id=settlement.market_id,
                    topic_title=topic.title if topic else "Unknown",
                    payout=user_settlement.payout,
                    winning_outcome_index=settlement.winning_outcome_index,
                )
            except Exception:
                pass  # Don't fail settlement if notification fails

        await self.db.flush()

        return paid_count

    async def create_dispute(self, settlement_id: str, user_id: str, reason: str, evidence: dict | None = None) -> SettlementDispute:
        """Create a settlement dispute."""
        dispute = SettlementDispute(
            settlement_id=settlement_id,
            user_id=user_id,
            reason=reason,
            evidence=evidence,
            status="pending",
        )

        self.db.add(dispute)

        # Update settlement status
        stmt = select(MarketSettlement).where(MarketSettlement.id == settlement_id)
        result = await self.db.execute(stmt)
        settlement = result.scalar_one_or_none()

        if settlement and settlement.status == "settling":
            settlement.status = "disputed"

        await self.db.flush()

        return dispute

    async def resolve_dispute(self, dispute_id: str, resolved_by: str, action: str, resolution: str) -> SettlementDispute:
        """Resolve a dispute."""
        stmt = select(SettlementDispute).where(SettlementDispute.id == dispute_id)
        result = await self.db.execute(stmt)
        dispute = result.scalar_one_or_none()

        if not dispute:
            raise ValueError("Dispute not found")

        dispute.status = "resolved" if action == "upheld" else "rejected"
        dispute.resolved_by = resolved_by
        dispute.resolved_at = datetime.utcnow()
        dispute.resolution = resolution

        # If dispute is upheld, may need to recalculate settlements
        # For now, just mark as resolved

        await self.db.flush()

        return dispute

    async def get_user_settlements(self, user_id: str, page: int = 1, limit: int = 20) -> tuple[list[UserSettlement], int]:
        """Get user's settlement history."""
        # Count total
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(UserSettlement).where(
            UserSettlement.user_id == user_id
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get settlements
        stmt = select(UserSettlement).where(
            UserSettlement.user_id == user_id
        ).order_by(UserSettlement.created_at.desc()).offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(stmt)
        settlements = list(result.scalars().all())

        return settlements, total
