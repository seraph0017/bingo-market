"""Trading service for prediction markets."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.topic import Topic, MarketPosition
from app.models.wallet import UserWallet
from app.services.lmsr import LMSREngine, LMSRState
from app.services.wallet import WalletService


class TradingService:
    """Prediction market trading business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.lmsr = LMSREngine(b=100.0)  # Default liquidity parameter
        self.wallet_service = WalletService(db)

    async def get_quote(self, topic_id: str, outcome_index: int, quantity: int) -> Dict:
        """
        Get a price quote for buying shares without actually executing the trade.

        Args:
            topic_id: Topic ID
            outcome_index: Index of outcome to buy
            quantity: Number of shares to buy

        Returns:
            Dictionary with cost, current_price, new_price, slippage
        """
        # Get topic
        topic_stmt = select(Topic).where(Topic.id == topic_id)
        topic_result = await self.db.execute(topic_stmt)
        topic = topic_result.scalar_one_or_none()

        if not topic:
            raise ValueError("Topic not found")

        if topic.status != "active":
            raise ValueError("Market is not active")

        if datetime.utcnow() > topic.expires_at:
            raise ValueError("Market has expired")

        if outcome_index < 0 or outcome_index >= len(topic.outcome_options):
            raise ValueError("Invalid outcome index")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        # Get current market state
        state = await self.get_market_state(topic_id)

        # Calculate cost
        new_state, cost, new_prices = self.lmsr.buy(state, outcome_index, quantity)

        if cost <= 0:
            cost = 0.0001

        cost_int = max(1, int(cost))

        # Get current prices
        current_prices = self.lmsr.get_prices(state)

        # Calculate slippage (price impact)
        current_price = current_prices[outcome_index]
        new_price = new_prices[outcome_index]
        slippage = ((new_price - current_price) / current_price * 100) if current_price > 0 else 0

        return {
            "cost": cost_int,
            "cost_raw": cost,
            "current_price": current_price,
            "new_price": new_price,
            "slippage_percent": round(slippage, 2),
            "quantity": quantity,
            "outcome_index": outcome_index,
        }

    async def get_sell_quote(self, topic_id: str, user_id: str, outcome_index: int, quantity: int) -> Dict:
        """
        Get a price quote for selling shares without actually executing the trade.

        Args:
            topic_id: Topic ID
            user_id: User ID
            outcome_index: Index of outcome to sell
            quantity: Number of shares to sell

        Returns:
            Dictionary with proceeds, current_price, new_price, slippage
        """
        # Get topic
        topic_stmt = select(Topic).where(Topic.id == topic_id)
        topic_result = await self.db.execute(topic_stmt)
        topic = topic_result.scalar_one_or_none()

        if not topic:
            raise ValueError("Topic not found")

        # Check user has position
        position_stmt = select(MarketPosition).where(
            MarketPosition.topic_id == topic_id,
            MarketPosition.user_id == user_id,
            MarketPosition.outcome_index == outcome_index,
        )
        position_result = await self.db.execute(position_stmt)
        position = position_result.scalar_one_or_none()

        if not position or position.shares < quantity:
            raise ValueError("Insufficient shares to sell")

        # Get current market state
        state = await self.get_market_state(topic_id)

        # Calculate proceeds (negative cost = money received)
        new_state, payout, new_prices = self.lmsr.sell(state, outcome_index, quantity)

        # Proceeds is the payout from LMSR
        proceeds = payout if payout > 0 else 0
        proceeds_int = max(0, int(proceeds))

        # Get current prices
        current_prices = self.lmsr.prices(state)
        current_price = current_prices[outcome_index]
        new_price = new_prices[outcome_index]
        slippage = ((current_price - new_price) / current_price * 100) if current_price > 0 else 0

        return {
            "proceeds": proceeds_int,
            "proceeds_raw": proceeds,
            "current_price": current_price,
            "new_price": new_price,
            "slippage_percent": round(slippage, 2),
            "quantity": quantity,
            "outcome_index": outcome_index,
        }

    async def get_market_state(self, topic_id: str) -> LMSRState:
        """Get current LMSR state for a topic."""
        stmt = select(MarketPosition).where(MarketPosition.topic_id == topic_id)
        result = await self.db.execute(stmt)
        positions = result.scalars().all()

        # Aggregate shares by outcome
        topic_stmt = select(Topic).where(Topic.id == topic_id)
        topic_result = await self.db.execute(topic_stmt)
        topic = topic_result.scalar_one_or_none()

        if not topic:
            raise ValueError("Topic not found")

        num_outcomes = len(topic.outcome_options)
        shares = [0] * num_outcomes

        for pos in positions:
            shares[pos.outcome_index] += pos.shares

        return LMSRState(shares=shares, b=self.lmsr.b)

    async def buy_shares(
        self,
        user_id: str,
        topic_id: str,
        outcome_index: int,
        quantity: int,
    ) -> Tuple[float, MarketPosition]:
        """
        Buy shares in a prediction market.

        Args:
            user_id: User ID
            topic_id: Topic ID
            outcome_index: Index of outcome to buy
            quantity: Number of shares to buy

        Returns:
            Tuple of (cost, user's updated position)
        """
        # Get topic
        topic_stmt = select(Topic).where(Topic.id == topic_id)
        topic_result = await self.db.execute(topic_stmt)
        topic = topic_result.scalar_one_or_none()

        if not topic:
            raise ValueError("Topic not found")

        if topic.status != "active":
            raise ValueError("Market is not active")

        if datetime.utcnow() > topic.expires_at:
            raise ValueError("Market has expired")

        if outcome_index < 0 or outcome_index >= len(topic.outcome_options):
            raise ValueError("Invalid outcome index")

        # Get current market state
        state = await self.get_market_state(topic_id)

        # Calculate cost
        new_state, cost, new_prices = self.lmsr.buy(state, outcome_index, quantity)

        if cost <= 0:
            cost = 0.0001  # Minimum cost to prevent free shares

        # Round to integer (knowledge coins)
        cost_int = max(1, int(cost))

        # Debit user wallet
        success = await self.wallet_service.debit_balance(
            user_id=user_id,
            amount=cost_int,
            transaction_type="prediction_purchase",
            reference_id=topic_id,
            description=f"Buy {quantity} shares of outcome {outcome_index}",
        )

        if not success:
            raise ValueError("Insufficient balance")

        # Update user position
        position_stmt = select(MarketPosition).where(
            MarketPosition.topic_id == topic_id,
            MarketPosition.user_id == user_id,
            MarketPosition.outcome_index == outcome_index,
        )
        position_result = await self.db.execute(position_stmt)
        position = position_result.scalar_one_or_none()

        if position:
            # Update existing position (average price)
            total_shares = position.shares + quantity
            total_cost = (position.avg_price * position.shares) + cost_int
            position.shares = total_shares
            position.avg_price = total_cost / total_shares if total_shares > 0 else 0
        else:
            # Create new position
            position = MarketPosition(
                user_id=user_id,
                topic_id=topic_id,
                outcome_index=outcome_index,
                shares=quantity,
                avg_price=cost_int / quantity if quantity > 0 else 0,
            )
            self.db.add(position)

        # Update topic stats
        topic.participant_count = await self._count_participants(topic_id)
        topic.trade_volume += cost_int

        await self.db.flush()

        return cost_int, position

    async def sell_shares(
        self,
        user_id: str,
        topic_id: str,
        outcome_index: int,
        quantity: int,
    ) -> Tuple[int, MarketPosition]:
        """
        Sell shares in a prediction market.

        Args:
            user_id: User ID
            topic_id: Topic ID
            outcome_index: Index of outcome to sell
            quantity: Number of shares to sell

        Returns:
            Tuple of (payout, user's updated position)
        """
        # Get topic
        topic_stmt = select(Topic).where(Topic.id == topic_id)
        topic_result = await self.db.execute(topic_stmt)
        topic = topic_result.scalar_one_or_none()

        if not topic:
            raise ValueError("Topic not found")

        if topic.status != "active":
            raise ValueError("Market is not active")

        if outcome_index < 0 or outcome_index >= len(topic.outcome_options):
            raise ValueError("Invalid outcome index")

        # Get user position
        position_stmt = select(MarketPosition).where(
            MarketPosition.topic_id == topic_id,
            MarketPosition.user_id == user_id,
            MarketPosition.outcome_index == outcome_index,
        )
        position_result = await self.db.execute(position_stmt)
        position = position_result.scalar_one_or_none()

        if not position or position.shares < quantity:
            raise ValueError("Insufficient shares")

        # Get current market state
        state = await self.get_market_state(topic_id)

        # Calculate payout
        new_state, payout, new_prices = self.lmsr.sell(state, outcome_index, quantity)

        # Round to integer
        payout_int = max(0, int(payout))

        # Credit user wallet
        await self.wallet_service.credit_balance(
            user_id=user_id,
            amount=payout_int,
            transaction_type="prediction_sale",
            reference_id=topic_id,
            description=f"Sell {quantity} shares of outcome {outcome_index}",
        )

        # Update position
        position.shares -= quantity
        if position.shares == 0:
            # Delete empty position (optional, could keep as 0)
            await self.db.delete(position)

        # Update topic stats
        topic.trade_volume += payout_int

        await self.db.flush()

        return payout_int, position

    async def _count_participants(self, topic_id: str) -> int:
        """Count unique participants in a topic."""
        stmt = select(func.count(MarketPosition.user_id.distinct())).where(
            MarketPosition.topic_id == topic_id
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_user_position(self, user_id: str, topic_id: str) -> MarketPosition | None:
        """Get user's total position in a topic (aggregated across outcomes)."""
        stmt = select(MarketPosition).where(
            MarketPosition.topic_id == topic_id,
            MarketPosition.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_user_positions(self, user_id: str, topic_id: str) -> list[MarketPosition]:
        """Get all user positions for a topic (all outcomes)."""
        stmt = select(MarketPosition).where(
            MarketPosition.topic_id == topic_id,
            MarketPosition.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _get_all_positions(self, user_id: str) -> list[MarketPosition]:
        """Get all user positions across all topics."""
        stmt = select(MarketPosition).where(MarketPosition.user_id == user_id)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
