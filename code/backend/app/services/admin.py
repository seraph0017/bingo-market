"""Admin service."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import joinedload

from app.models.user import User
from app.models.wallet import UserWallet, RechargeOrder, WalletTransaction
from app.models.topic import Topic, TopicReview, CreatorProfile
from app.models.settlement import MarketSettlement
from app.models.product import Product, ExchangeOrder


class AdminService:
    """Admin business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_metrics(self) -> dict:
        """Get dashboard metrics."""
        # User metrics
        total_users = await self._count(User)
        active_users_24h = await self._count_active_users_24h()

        # Transaction metrics
        total_transactions = await self._count(WalletTransaction)
        total_volume = await self._sum_wallet_transactions()

        # Market metrics
        active_topics = await self._count_by_status(Topic, "active")
        pending_reviews = await self._count_pending_reviews()

        # System status
        system_status = "healthy"

        return {
            "total_users": total_users,
            "active_users_24h": active_users_24h,
            "total_transactions": total_transactions,
            "total_volume": total_volume,
            "active_topics": active_topics,
            "pending_reviews": pending_reviews,
            "system_status": system_status,
        }

    async def get_products(
        self,
        status: str | None = None,
        category_id: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Product], int]:
        """Get products with filtering."""
        filters = []
        if status:
            filters.append(Product.status == status)
        if category_id:
            filters.append(Product.category_id == category_id)

        # Count
        count_stmt = select(func.count()).select_from(Product)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get products
        stmt = select(Product)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(desc(Product.created_at)).offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(stmt)
        products = list(result.scalars().all())

        return products, total

    async def update_product_status(self, product_id: str, status: str) -> Product:
        """Update product status."""
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        product = result.scalar_one_or_none()

        if not product:
            raise ValueError("Product not found")

        product.status = status
        await self.db.flush()
        return product

    async def _count(self, model) -> int:
        """Count all records in a model."""
        stmt = select(func.count()).select_from(model)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _count_active_users_24h(self) -> int:
        """Count users active in last 24 hours."""
        from app.models.user import User
        cutoff = datetime.utcnow() - timedelta(hours=24)
        stmt = select(func.count()).select_from(User).where(
            User.last_login_at >= cutoff
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _count_wallet_transactions(self) -> int:
        """Count wallet transactions."""
        stmt = select(func.count()).select_from(WalletTransaction)
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _sum_wallet_transactions(self) -> int:
        """Sum of all transaction amounts."""
        stmt = select(func.sum(WalletTransaction.balance_after))
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _count_by_status(self, model, status: str) -> int:
        """Count records by status."""
        stmt = select(func.count()).select_from(model).where(
            model.status == status
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def _count_pending_reviews(self) -> int:
        """Count pending topic reviews."""
        stmt = select(func.count()).select_from(Topic).where(
            Topic.status == "pending_review"
        )
        result = await self.db.execute(stmt)
        return result.scalar() or 0

    async def get_users(
        self,
        status: str | None = None,
        role: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        """Get users with filtering."""
        filters = []
        if status:
            filters.append(User.status == status)
        if role:
            filters.append(User.role == role)

        # Count
        count_stmt = select(func.count()).select_from(User)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get users
        stmt = select(User)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(desc(User.created_at)).offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(stmt)
        users = list(result.scalars().all())

        return users, total

    async def get_user_detail(self, user_id: str) -> User | None:
        """Get user detail."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_user_status(self, user_id: str, status: str, updated_by: str) -> User:
        """Update user status."""
        user = await self.get_user_detail(user_id)
        if not user:
            raise ValueError("User not found")

        user.status = status
        user.updated_at = datetime.utcnow()
        await self.db.flush()
        return user

    async def freeze_user(self, user_id: str, reason: str, frozen_by: str, duration_days: Optional[int] = None) -> User:
        """Freeze user account."""
        user = await self.get_user_detail(user_id)
        if not user:
            raise ValueError("User not found")

        user.status = "frozen"
        user.updated_at = datetime.utcnow()
        await self.db.flush()

        # TODO: Log freeze action to audit log
        return user

    async def unfreeze_user(self, user_id: str, reason: str, unfrozen_by: str) -> User:
        """Unfreeze user account."""
        user = await self.get_user_detail(user_id)
        if not user:
            raise ValueError("User not found")

        if user.status != "frozen":
            raise ValueError("User is not frozen")

        user.status = "unverified"
        user.updated_at = datetime.utcnow()
        await self.db.flush()

        # TODO: Log unfreeze action to audit log
        return user

    async def get_pending_reviews(
        self, page: int = 1, limit: int = 20
    ) -> tuple[list[Topic], int]:
        """Get pending content reviews."""
        # Count
        count_stmt = select(func.count()).select_from(Topic).where(
            Topic.status == "pending_review"
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get topics
        stmt = (
            select(Topic)
            .where(Topic.status == "pending_review")
            .order_by(Topic.created_at.asc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        topics = list(result.scalars().all())

        return topics, total

    async def get_recharge_records(
        self,
        status: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[RechargeOrder], int]:
        """Get recharge records."""
        filters = []
        if status:
            filters.append(RechargeOrder.status == status)

        # Count
        count_stmt = select(func.count()).select_from(RechargeOrder)
        if filters:
            count_stmt = count_stmt.where(and_(*filters))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get orders
        stmt = select(RechargeOrder)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.order_by(desc(RechargeOrder.created_at)).offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())

        return orders, total

    async def get_audit_logs(
        self,
        admin_id: str | None = None,
        action: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list, int]:
        """Get audit logs (placeholder - would need AuditLog model)."""
        # TODO: Implement audit log model
        return [], 0
