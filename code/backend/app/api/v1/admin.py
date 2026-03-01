"""Admin API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.core.security import verify_token
from app.services.admin import AdminService
from app.services.wallet import WalletService
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Annotated


router = APIRouter()
security = HTTPBearer()


class UserActionRequest(BaseModel):
    """User action request."""

    action: str  # freeze, unfreeze, ban, verify
    reason: str | None = None
    duration_days: int | None = None  # For freeze action


class ProductActionRequest(BaseModel):
    """Product action request."""

    reason: str | None = None


class BalanceAdjustmentRequest(BaseModel):
    """Balance adjustment request (admin only)."""

    amount: int = Field(..., description="Amount to adjust (positive for credit, negative for debit)")
    reason: str = Field(..., description="Reason for adjustment")


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current user ID from token."""
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


async def get_admin_service(db: AsyncSession = Depends(get_db)) -> AdminService:
    """Get admin service dependency."""
    return AdminService(db)


async def get_wallet_service(db: AsyncSession = Depends(get_db)) -> WalletService:
    """Get wallet service dependency."""
    return WalletService(db)


AdminServiceDep = Annotated[AdminService, Depends(get_admin_service)]
WalletServiceDep = Annotated[WalletService, Depends(get_wallet_service)]


@router.get("/dashboard")
async def get_dashboard(
    admin_service: AdminService = Depends(get_admin_service),
):
    """Get dashboard metrics."""
    metrics = await admin_service.get_dashboard_metrics()
    return metrics


@router.get("/users")
async def list_users(
    status: str | None = Query(None),
    role: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin_service: AdminService = Depends(get_admin_service),
):
    """List users for management."""
    users, total = await admin_service.get_users(
        status=status, role=role, page=page, limit=limit
    )

    return {
        "users": [
            {
                "id": u.id,
                "phone": u.phone[:7] + "****" if u.phone else None,
                "email": u.email,
                "full_name": u.full_name,
                "status": u.status,
                "role": u.role,
                "created_at": u.created_at,
                "last_login_at": u.last_login_at,
            }
            for u in users
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/users/{user_id}")
async def get_user_detail(
    user_id: str,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Get user details."""
    user = await admin_service.get_user_detail(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get wallet
    from sqlalchemy import select
    from app.models.wallet import UserWallet
    stmt = select(UserWallet).where(UserWallet.user_id == user_id)
    result = await admin_service.db.execute(stmt)
    wallet = result.scalar_one_or_none()

    return {
        "user": {
            "id": user.id,
            "phone": user.phone,
            "email": user.email,
            "full_name": user.full_name,
            "id_number": user.id_number[:6] + "****" if user.id_number else None,
            "birth_date": user.birth_date,
            "status": user.status,
            "role": user.role,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
        },
        "wallet": {
            "balance": wallet.balance if wallet else 0,
            "status": wallet.status if wallet else "inactive",
        } if wallet else None,
    }


@router.post("/users/{user_id}/actions")
async def user_action(
    user_id: str,
    data: UserActionRequest,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Perform action on user (freeze, ban, verify)."""
    try:
        if data.action in ["freeze", "ban", "verify", "unverified"]:
            user = await admin_service.update_user_status(user_id, data.action)
            return {"message": "Success", "new_status": user.status}
        elif data.action == "freeze_user":
            user = await admin_service.freeze_user(
                user_id, data.reason or "", "admin", data.duration_days
            )
            return {"message": "User frozen", "new_status": user.status}
        elif data.action == "unfreeze_user":
            user = await admin_service.unfreeze_user(user_id, data.reason or "", "admin")
            return {"message": "User unfrozen", "new_status": user.status}
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/users/{user_id}/balance")
async def adjust_balance(
    user_id: str,
    data: BalanceAdjustmentRequest,
    current_user_id: str = Depends(get_current_user_id),
    admin_service: AdminService = Depends(get_admin_service),
    wallet_service: WalletService = Depends(get_wallet_service),
):
    """Adjust user balance (customer service scenario)."""
    # Note: This requires careful audit logging in production
    if data.amount > 0:
        success = await wallet_service.credit_balance(
            user_id=user_id,
            amount=data.amount,
            transaction_type="admin_adjustment",
            description=f"Admin adjustment: {data.reason}",
        )
    else:
        success = await wallet_service.debit_balance(
            user_id=user_id,
            amount=abs(data.amount),
            transaction_type="admin_adjustment",
            description=f"Admin adjustment: {data.reason}",
        )

    if not success:
        raise HTTPException(status_code=400, detail="Failed to adjust balance")

    return {"message": "Balance adjusted", "amount": data.amount}


@router.get("/reviews/pending")
async def get_pending_reviews(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Get pending content reviews."""
    topics, total = await admin_service.get_pending_reviews(page=page, limit=limit)

    return {
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "category": t.category,
                "creator_id": t.creator_id,
                "created_at": t.created_at,
            }
            for t in topics
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/recharge/records")
async def get_recharge_records(
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Get recharge records."""
    orders, total = await admin_service.get_recharge_records(
        status=status, page=page, limit=limit
    )

    return {
        "orders": [
            {
                "order_id": o.id,
                "user_id": o.user_id,
                "amount_vnd": o.amount_vnd,
                "amount_tokens": o.amount_tokens,
                "payment_method": o.payment_method,
                "status": o.status,
                "created_at": o.created_at,
                "paid_at": o.paid_at,
            }
            for o in orders
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/audit-logs")
async def get_audit_logs(
    admin_id: str | None = Query(None),
    action: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Get audit logs."""
    # TODO: Implement audit log model
    return {"logs": [], "total": 0, "page": page, "limit": limit}


@router.get("/products")
async def list_products(
    status: str | None = Query(None),
    category_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    admin_service: AdminService = Depends(get_admin_service),
):
    """List products for management."""
    products, total = await admin_service.get_products(
        status=status, category_id=category_id, page=page, limit=limit
    )

    return {
        "products": [
            {
                "id": p.id,
                "title": p.title,
                "category_id": p.category_id,
                "price": p.price,
                "inventory_count": p.inventory_count,
                "sold_count": p.sold_count,
                "status": p.status,
                "supplier_id": p.supplier_id,
                "created_at": p.created_at,
            }
            for p in products
        ],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.post("/products/{product_id}/activate")
async def activate_product(
    product_id: str,
    data: ProductActionRequest | None = None,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Activate product (admin only)."""
    try:
        product = await admin_service.update_product_status(product_id, "active")
        return {"message": "Product activated", "status": product.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/products/{product_id}/deactivate")
async def deactivate_product(
    product_id: str,
    data: ProductActionRequest | None = None,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Deactivate product (admin only)."""
    try:
        product = await admin_service.update_product_status(product_id, "inactive")
        return {"message": "Product deactivated", "status": product.status}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
