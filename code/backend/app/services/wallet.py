"""Wallet service."""

from __future__ import annotations

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.wallet import UserWallet, RechargeOrder, WalletTransaction
from app.models.user import User
from app.core.config import settings
from app.schemas.wallet import CreateRechargeOrderRequest


class WalletService:
    """Wallet business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_wallet(self, user_id: str) -> UserWallet:
        """Get or create user wallet."""
        stmt = select(UserWallet).where(UserWallet.user_id == user_id)
        result = await self.db.execute(stmt)
        wallet = result.scalar_one_or_none()

        if not wallet:
            wallet = UserWallet(user_id=user_id, balance=0)
            self.db.add(wallet)
            await self.db.flush()

        return wallet

    async def get_wallet_info(self, user_id: str) -> dict:
        """Get wallet info with limits."""
        wallet = await self.get_or_create_wallet(user_id)

        # Get user verification status
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        # Reset daily limit if new day
        today = date.today()
        if wallet.daily_recharged_date and wallet.daily_recharged_date.date() != today:
            wallet.daily_recharged = 0
            wallet.daily_recharged_date = datetime.now()

        # Reset monthly limit if new month
        current_month = today.month
        if wallet.monthly_recharged_month != current_month:
            wallet.monthly_recharged = 0
            wallet.monthly_recharged_month = current_month

        await self.db.flush()

        return {
            "balance": wallet.balance,
            "daily_limit_remaining": settings.vnd_daily_limit - wallet.daily_recharged,
            "monthly_limit_remaining": settings.vnd_monthly_limit - wallet.monthly_recharged,
            "is_verified": user.status == "verified_18plus" if user else False,
            "status": wallet.status,
        }

    async def create_recharge_order(
        self, user_id: str, data: CreateRechargeOrderRequest
    ) -> RechargeOrder:
        """Create recharge order."""
        # Get wallet and check limits
        wallet = await self.get_or_create_wallet(user_id)

        # Reset limits if needed
        today = date.today()
        if wallet.daily_recharged_date and wallet.daily_recharged_date.date() != today:
            wallet.daily_recharged = 0
            wallet.daily_recharged_date = datetime.now()

        current_month = today.month
        if wallet.monthly_recharged_month != current_month:
            wallet.monthly_recharged = 0
            wallet.monthly_recharged_month = current_month

        # Check limits
        remaining_daily = settings.vnd_daily_limit - wallet.daily_recharged
        remaining_monthly = settings.vnd_monthly_limit - wallet.monthly_recharged

        if data.amount > remaining_daily:
            raise ValueError(f"Exceeds daily limit. Remaining: {remaining_daily} VND")
        if data.amount > remaining_monthly:
            raise ValueError(f"Exceeds monthly limit. Remaining: {remaining_monthly} VND")

        # Check user verification
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_stmt)
        user = user_result.scalar_one_or_none()

        if not user or user.status != "verified_18plus":
            raise ValueError("Must complete 18+ verification to recharge")

        # Create order (1 VND = 1 knowledge coin)
        order = RechargeOrder(
            user_id=user_id,
            amount_vnd=data.amount,
            amount_tokens=data.amount,  # 1:1 ratio
            payment_method=data.payment_method,
            status="pending",
            daily_limit_used=wallet.daily_recharged,
            monthly_limit_used=wallet.monthly_recharged,
        )

        self.db.add(order)
        await self.db.flush()

        return order

    async def complete_recharge(self, order_id: str, external_order_id: str | None = None) -> bool:
        """Complete recharge order and credit wallet."""
        stmt = select(RechargeOrder).where(RechargeOrder.id == order_id)
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order or order.status != "pending":
            return False

        # Update order status
        order.status = "success"
        order.external_order_id = external_order_id
        order.paid_at = datetime.utcnow()

        # Credit wallet
        wallet = await self.get_or_create_wallet(order.user_id)
        wallet.balance += order.amount_tokens
        wallet.daily_recharged += order.amount_vnd
        wallet.monthly_recharged += order.amount_vnd
        wallet.daily_recharged_date = datetime.now()
        wallet.monthly_recharged_month = date.today().month

        # Create transaction record
        transaction = WalletTransaction(
            wallet_id=wallet.id,
            amount=order.amount_tokens,
            balance_after=wallet.balance,
            transaction_type="recharge",
            reference_id=order.id,
            description=f"Recharge {order.amount_vnd} VND",
        )
        self.db.add(transaction)

        await self.db.flush()
        return True

    async def debit_balance(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        reference_id: str | None = None,
        description: str | None = None,
    ) -> bool:
        """Debit from wallet balance."""
        wallet = await self.get_or_create_wallet(user_id)

        if wallet.balance < amount:
            return False
        if wallet.status != "active":
            return False

        wallet.balance -= amount

        transaction = WalletTransaction(
            wallet_id=wallet.id,
            amount=-amount,
            balance_after=wallet.balance,
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description,
        )
        self.db.add(transaction)

        await self.db.flush()
        return True

    async def credit_balance(
        self,
        user_id: str,
        amount: int,
        transaction_type: str,
        reference_id: str | None = None,
        description: str | None = None,
    ) -> bool:
        """Credit to wallet balance."""
        wallet = await self.get_or_create_wallet(user_id)

        if wallet.status != "active":
            return False

        wallet.balance += amount

        transaction = WalletTransaction(
            wallet_id=wallet.id,
            amount=amount,
            balance_after=wallet.balance,
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description,
        )
        self.db.add(transaction)

        await self.db.flush()
        return True

    async def get_recharge_records(
        self, user_id: str, page: int = 1, limit: int = 20
    ) -> tuple[list[RechargeOrder], int]:
        """Get user recharge records (last 30 days)."""
        from sqlalchemy import and_
        from datetime import timedelta

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # Count total
        count_stmt = select(func.count()).select_from(RechargeOrder).where(
            and_(
                RechargeOrder.user_id == user_id,
                RechargeOrder.created_at >= thirty_days_ago,
            )
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get records
        stmt = (
            select(RechargeOrder)
            .where(
                and_(
                    RechargeOrder.user_id == user_id,
                    RechargeOrder.created_at >= thirty_days_ago,
                )
            )
            .order_by(RechargeOrder.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        orders = result.scalars().all()

        return list(orders), total

    async def get_transaction_records(
        self, user_id: str, page: int = 1, limit: int = 20
    ) -> tuple[list[WalletTransaction], int]:
        """Get user transaction records."""
        wallet = await self.get_or_create_wallet(user_id)

        # Count total
        count_stmt = select(func.count()).select_from(WalletTransaction).where(
            WalletTransaction.wallet_id == wallet.id
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get records
        stmt = (
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet.id)
            .order_by(WalletTransaction.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        transactions = result.scalars().all()

        return list(transactions), total

    async def get_recharge_order(self, order_id: str, user_id: str) -> RechargeOrder | None:
        """Get recharge order by ID."""
        stmt = select(RechargeOrder).where(
            RechargeOrder.id == order_id,
            RechargeOrder.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
