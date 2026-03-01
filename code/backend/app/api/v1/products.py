"""Products API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.product import (
    ProductInfo,
    ProductDetail,
    ProductListResponse,
    CreateProductRequest,
    ExchangeOrderResponse,
    UserProductInfo,
    ProductListResponse as ProductListResponseSchema,
)
from app.services.product import ProductService
from app.core.database import get_db
from app.core.security import verify_token
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime


router = APIRouter()
security = HTTPBearer()


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current user ID from token."""
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


async def get_product_service(db: AsyncSession = Depends(get_db)) -> ProductService:
    """Get product service dependency."""
    return ProductService(db)


@router.get("/", response_model=ProductListResponse)
async def list_products(
    category_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    product_service: ProductService = Depends(get_product_service),
):
    """List products."""
    products, total = await product_service.get_products(
        category_id=category_id, page=page, limit=limit
    )

    product_list = [
        ProductInfo(
            id=p.id,
            title=p.title,
            description=p.description,
            category_id=p.category_id,
            price=p.price,
            inventory_type=p.inventory_type,
            inventory_count=p.inventory_count,
            sold_count=p.sold_count,
            product_type=p.product_type,
            status=p.status,
        )
        for p in products
    ]

    return ProductListResponse(products=product_list, total=total, page=page, limit=limit)


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    user_id: str = Depends(get_current_user_id),
    product_service: ProductService = Depends(get_product_service),
):
    """Get product details."""
    product = await product_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get user balance
    wallet = await product_service.wallet_service.get_or_create_wallet(user_id)

    return ProductDetail(
        id=product.id,
        title=product.title,
        description=product.description,
        category_id=product.category_id,
        price=product.price,
        inventory_type=product.inventory_type,
        inventory_count=product.inventory_count,
        sold_count=product.sold_count,
        product_type=product.product_type,
        status=product.status,
        delivery_config=product.delivery_config,
        supplier_id=product.supplier_id,
        created_at=product.created_at,
        can_exchange=wallet.balance >= product.price,
        user_balance=wallet.balance,
    )


@router.post("/{product_id}/exchange", response_model=ExchangeOrderResponse)
async def exchange_product(
    product_id: str,
    quantity: int = Query(1, ge=1),
    user_id: str = Depends(get_current_user_id),
    product_service: ProductService = Depends(get_product_service),
):
    """Redeem product with knowledge coins."""
    try:
        order, user_product = await product_service.exchange_product(
            user_id=user_id, product_id=product_id, quantity=quantity
        )

        return ExchangeOrderResponse(
            order_id=order.id,
            product_id=order.product_id,
            quantity=order.quantity,
            total_price=order.total_price,
            status=order.status,
            delivery_info=order.delivery_info,
            created_at=order.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/exchange/orders")
async def get_exchange_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    product_service: ProductService = Depends(get_product_service),
):
    """Get exchange order history."""
    orders, total = await product_service.get_user_orders(user_id, page, limit)

    return {
        "orders": [
            {
                "order_id": o.id,
                "product_id": o.product_id,
                "quantity": o.quantity,
                "total_price": o.total_price,
                "status": o.status,
                "created_at": o.created_at,
            }
            for o in orders
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/my-products")
async def get_user_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    product_service: ProductService = Depends(get_product_service),
):
    """Get user's owned products."""
    products, total = await product_service.get_user_products(user_id, page, limit)

    return {
        "products": [
            {
                "id": p.id,
                "product_id": p.product_id,
                "delivery_code": p.delivery_code,
                "access_url": p.access_url,
                "expires_at": p.expires_at,
                "is_used": p.is_used,
                "created_at": p.created_at,
            }
            for p in products
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/search", response_model=ProductListResponse)
async def search_products(
    q: str = Query(..., min_length=1, description="Search query"),
    category_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    product_service: ProductService = Depends(get_product_service),
):
    """Search products by keyword."""
    try:
        products, total = await product_service.search_products(
            query=q, category_id=category_id, page=page, limit=limit
        )

        product_list = [
            ProductInfo(
                id=p.id,
                title=p.title,
                description=p.description,
                category_id=p.category_id,
                price=p.price,
                inventory_type=p.inventory_type,
                inventory_count=p.inventory_count,
                sold_count=p.sold_count,
                product_type=p.product_type,
                status=p.status,
            )
            for p in products
        ]

        return ProductListResponse(products=product_list, total=total, page=page, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
