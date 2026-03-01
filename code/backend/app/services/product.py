"""Product service."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.product import Product, ProductCategory, ExchangeOrder, UserProduct
from app.models.wallet import UserWallet
from app.services.wallet import WalletService
from app.schemas.product import CreateProductRequest


class ProductService:
    """Product business logic."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.wallet_service = WalletService(db)

    async def get_products(
        self,
        category_id: str | None = None,
        status: str = "active",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Product], int]:
        """Get products with filtering."""
        # Build filters
        filters = [Product.status == status]
        if category_id:
            filters.append(Product.category_id == category_id)

        # Count total
        count_stmt = select(func.count()).select_from(Product).where(and_(*filters))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get products
        stmt = (
            select(Product)
            .where(and_(*filters))
            .order_by(Product.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        products = list(result.scalars().all())

        return products, total

    async def get_product(self, product_id: str) -> Product | None:
        """Get product by ID."""
        stmt = select(Product).where(Product.id == product_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_product(self, supplier_id: str, data: CreateProductRequest) -> Product:
        """Create a new product."""
        product = Product(
            title=data.title,
            description=data.description,
            category_id=data.category_id,
            price=data.price,
            inventory_type=data.inventory_type,
            inventory_count=data.inventory_count,
            product_type=data.product_type,
            delivery_config=data.delivery_config,
            supplier_id=supplier_id,
            status="pending",  # Needs admin approval
        )

        self.db.add(product)
        await self.db.flush()

        return product

    async def exchange_product(
        self, user_id: str, product_id: str, quantity: int = 1
    ) -> tuple[ExchangeOrder, UserProduct | None]:
        """Exchange product with knowledge coins."""
        # Get product
        product = await self.get_product(product_id)
        if not product:
            raise ValueError("Product not found")

        if product.status != "active":
            raise ValueError("Product not available")

        # Check inventory
        if product.inventory_type == "limited":
            if product.inventory_count is None or product.inventory_count < quantity:
                raise ValueError("Insufficient inventory")

        # Calculate total price
        total_price = product.price * quantity

        # Debit user wallet
        success = await self.wallet_service.debit_balance(
            user_id=user_id,
            amount=total_price,
            transaction_type="purchase",
            reference_id=product_id,
            description=f"Purchase {product.title} x{quantity}",
        )

        if not success:
            raise ValueError("Insufficient balance")

        # Create exchange order
        order = ExchangeOrder(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity,
            total_price=total_price,
            status="processing",
        )
        self.db.add(order)
        await self.db.flush()

        # Update inventory
        if product.inventory_type == "limited":
            product.inventory_count -= quantity
        product.sold_count += quantity

        # Deliver product
        user_product = None
        delivery_info = {}

        if product.product_type == "digital":
            # Digital content - grant access
            access_url = product.delivery_config.get("access_url", "")
            valid_days = product.delivery_config.get("valid_days", 30)
            expires_at = datetime.utcnow() + timedelta(days=valid_days)

            user_product = UserProduct(
                user_id=user_id,
                product_id=product_id,
                order_id=order.id,
                access_url=access_url,
                expires_at=expires_at,
                is_used=False,
            )
            delivery_info["access_url"] = access_url
            delivery_info["expires_at"] = expires_at.isoformat()

        elif product.product_type == "service":
            # Service voucher - generate code
            import secrets
            delivery_code = f"{secrets.token_hex(8).upper()}-{secrets.token_hex(4).upper()}"
            valid_days = product.delivery_config.get("valid_days", 30)
            expires_at = datetime.utcnow() + timedelta(days=valid_days)

            user_product = UserProduct(
                user_id=user_id,
                product_id=product_id,
                order_id=order.id,
                delivery_code=delivery_code,
                expires_at=expires_at,
                is_used=False,
            )
            delivery_info["delivery_code"] = delivery_code
            delivery_info["expires_at"] = expires_at.isoformat()

        elif product.product_type == "membership":
            # Membership - activate immediately
            valid_days = product.delivery_config.get("valid_days", 30)
            expires_at = datetime.utcnow() + timedelta(days=valid_days)

            user_product = UserProduct(
                user_id=user_id,
                product_id=product_id,
                order_id=order.id,
                expires_at=expires_at,
                is_used=True,  # Auto-activated
                used_at=datetime.utcnow(),
            )
            delivery_info["expires_at"] = expires_at.isoformat()
            delivery_info["activated"] = True

        elif product.product_type == "virtual":
            # Virtual item - permanent
            user_product = UserProduct(
                user_id=user_id,
                product_id=product_id,
                order_id=order.id,
                is_used=True,  # Auto-equipped
                used_at=datetime.utcnow(),
            )
            delivery_info["equipped"] = True

        if user_product:
            self.db.add(user_product)

        # Update order status and delivery info
        order.status = "delivered"
        order.delivery_info = delivery_info

        await self.db.flush()

        return order, user_product

    async def get_user_orders(self, user_id: str, page: int = 1, limit: int = 20) -> tuple[list[ExchangeOrder], int]:
        """Get user's exchange orders."""
        # Count total
        count_stmt = select(func.count()).select_from(ExchangeOrder).where(
            ExchangeOrder.user_id == user_id
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get orders
        stmt = (
            select(ExchangeOrder)
            .where(ExchangeOrder.user_id == user_id)
            .order_by(ExchangeOrder.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())

        return orders, total

    async def get_user_products(self, user_id: str, page: int = 1, limit: int = 20) -> tuple[list[UserProduct], int]:
        """Get user's owned products."""
        # Count total
        count_stmt = select(func.count()).select_from(UserProduct).where(
            UserProduct.user_id == user_id
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get products
        stmt = (
            select(UserProduct)
            .where(UserProduct.user_id == user_id)
            .order_by(UserProduct.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        products = list(result.scalars().all())

        return products, total

    async def refund_failed_delivery(self, order_id: str) -> bool:
        """Refund user for failed delivery."""
        # Get order
        stmt = select(ExchangeOrder).where(ExchangeOrder.id == order_id)
        result = await self.db.execute(stmt)
        order = result.scalar_one_or_none()

        if not order:
            raise ValueError("Order not found")

        if order.status != "processing":
            raise ValueError("Order is not in processing state")

        # Refund user wallet
        success = await self.wallet_service.credit_balance(
            user_id=order.user_id,
            amount=order.total_price,
            transaction_type="refund",
            reference_id=order_id,
            description=f"Refund for failed delivery of order {order_id}",
        )

        if success:
            # Update order status
            order.status = "failed"
            await self.db.flush()

        return success

    async def get_exchange_records(
        self, user_id: str, page: int = 1, limit: int = 20
    ) -> tuple[list[ExchangeOrder], int]:
        """Get user's exchange records (last 30 days)."""
        from datetime import timedelta

        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # Count total
        count_stmt = select(func.count()).select_from(ExchangeOrder).where(
            and_(
                ExchangeOrder.user_id == user_id,
                ExchangeOrder.created_at >= thirty_days_ago,
            )
        )
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get records
        stmt = (
            select(ExchangeOrder)
            .where(
                and_(
                    ExchangeOrder.user_id == user_id,
                    ExchangeOrder.created_at >= thirty_days_ago,
                )
            )
            .order_by(ExchangeOrder.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        orders = list(result.scalars().all())

        return orders, total

    async def search_products(
        self,
        query: str,
        category_id: str | None = None,
        status: str = "active",
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Product], int]:
        """Search products by keyword."""
        from sqlalchemy import or_

        # Build filters
        filters = [Product.status == status]
        if category_id:
            filters.append(Product.category_id == category_id)

        # Search in title and description
        search_filter = or_(
            Product.title.ilike(f"%{query}%"),
            Product.description.ilike(f"%{query}%"),
        )
        filters.append(search_filter)

        # Count total
        count_stmt = select(func.count()).select_from(Product).where(and_(*filters))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get products
        stmt = (
            select(Product)
            .where(and_(*filters))
            .order_by(Product.sold_count.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        products = list(result.scalars().all())

        return products, total
