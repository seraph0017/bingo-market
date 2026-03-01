"""Product schemas."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


# Request schemas
class CreateProductRequest(BaseModel):
    """Create product request."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10, max_length=2000)
    category_id: str
    price: int = Field(..., gt=0)
    inventory_type: str = "unlimited"  # limited/unlimited
    inventory_count: int | None = None
    product_type: str = Field(...)  # digital, service, membership, virtual
    delivery_config: dict


class ExchangeProductRequest(BaseModel):
    """Exchange product request."""

    quantity: int = Field(1, ge=1)


# Response schemas
class ProductInfo(BaseModel):
    """Product information."""

    id: str
    title: str
    description: str
    category_id: str
    price: int
    inventory_type: str
    inventory_count: int | None = None
    sold_count: int
    product_type: str
    status: str


class ProductDetail(ProductInfo):
    """Product detail with full information."""

    delivery_config: dict
    supplier_id: str
    created_at: datetime
    can_exchange: bool = True
    user_balance: int | None = None


class ProductListResponse(BaseModel):
    """Paginated product list response."""

    products: list[ProductInfo]
    total: int
    page: int
    limit: int


class ExchangeOrderResponse(BaseModel):
    """Exchange order response."""

    order_id: str
    product_id: str
    quantity: int
    total_price: int
    status: str
    delivery_info: dict | None = None
    created_at: datetime


class UserProductInfo(BaseModel):
    """User's owned product information."""

    id: str
    product_id: str
    product_title: str
    delivery_code: str | None = None
    access_url: str | None = None
    expires_at: datetime | None = None
    is_used: bool
    created_at: datetime
