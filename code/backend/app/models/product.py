"""Mall/Product database models."""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, BigInteger, DateTime, Integer, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4

from app.core.database import Base


class ProductCategory(Base):
    """Product category."""

    __tablename__ = "product_categories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100))
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("product_categories.id"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<ProductCategory {self.id} name='{self.name}'>"


class Product(Base):
    """Product in the knowledge coin mall."""

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)

    # Category
    category_id: Mapped[str] = mapped_column(String(36), ForeignKey("product_categories.id"), index=True)

    # Price in knowledge coins
    price: Mapped[int] = mapped_column(BigInteger)

    # Inventory: limited or unlimited
    inventory_type: Mapped[str] = mapped_column(String(20), default="unlimited")  # limited/unlimited
    inventory_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # For limited type
    sold_count: Mapped[int] = mapped_column(Integer, default=0)

    # Product type: digital, service, membership, virtual
    product_type: Mapped[str] = mapped_column(String(50))

    # Delivery configuration (access URL, validity period, etc.)
    delivery_config: Mapped[dict] = mapped_column(JSONB)

    # Status: draft, pending, active, inactive
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # Supplier (user who created the product)
    supplier_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Product {self.id} title='{self.title}'>"


class ExchangeOrder(Base):
    """Exchange order (product redemption with knowledge coins)."""

    __tablename__ = "exchange_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"), index=True)

    # Quantity and price
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    total_price: Mapped[int] = mapped_column(BigInteger)

    # Delivery information (access code, URL, etc.)
    delivery_info: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Status: processing, delivered, failed, cancelled
    status: Mapped[str] = mapped_column(String(20), default="processing")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<ExchangeOrder {self.id} user={self.user_id} product={self.product_id}>"


class UserProduct(Base):
    """User's owned products."""

    __tablename__ = "user_products"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    product_id: Mapped[str] = mapped_column(String(36), ForeignKey("products.id"))
    order_id: Mapped[str] = mapped_column(String(36), ForeignKey("exchange_orders.id"))

    # Delivery details
    delivery_code: Mapped[str | None] = mapped_column(String(100), nullable=True)  # For service vouchers
    access_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # For digital content

    # Expiration
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Usage status
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<UserProduct {self.id} user={self.user_id}>"
