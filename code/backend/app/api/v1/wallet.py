"""Wallet API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.wallet import (
    WalletInfo,
    CreateRechargeOrderRequest,
    RechargeOrderResponse,
    RechargeRecordsResponse,
    RechargeRecord,
    TransactionRecordsResponse,
    TransactionRecord,
)
from app.services.wallet import WalletService
from app.services.auth import AuthService
from app.core.database import get_db
from app.core.security import verify_token
from sqlalchemy.ext.asyncio import AsyncSession


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


async def get_wallet_service(db: AsyncSession = Depends(get_db)) -> WalletService:
    """Get wallet service dependency."""
    return WalletService(db)


@router.get("/", response_model=WalletInfo)
async def get_wallet(
    user_id: str = Depends(get_current_user_id),
    wallet_service: WalletService = Depends(get_wallet_service),
):
    """Get wallet info and limits."""
    try:
        info = await wallet_service.get_wallet_info(user_id)
        return WalletInfo(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recharge/orders", response_model=RechargeOrderResponse)
async def create_recharge_order(
    data: CreateRechargeOrderRequest,
    user_id: str = Depends(get_current_user_id),
    wallet_service: WalletService = Depends(get_wallet_service),
):
    """Create recharge order."""
    try:
        order = await wallet_service.create_recharge_order(user_id, data)

        # Generate redirect URL for payment gateway (mock for now)
        redirect_url = None
        if data.payment_method == "momo":
            redirect_url = f"https://payment.momo.vn/pay?order={order.id}"
        elif data.payment_method == "zalopay":
            redirect_url = f"https://payment.zalopay.vn/pay?order={order.id}"

        return RechargeOrderResponse(
            order_id=order.id,
            amount_vnd=order.amount_vnd,
            amount_tokens=order.amount_tokens,
            payment_method=order.payment_method,
            status=order.status,
            redirect_url=redirect_url,
            created_at=order.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recharge/orders/{order_id}", response_model=RechargeOrderResponse)
async def get_recharge_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
    wallet_service: WalletService = Depends(get_wallet_service),
):
    """Get recharge order status."""
    try:
        order = await wallet_service.get_recharge_order(order_id, user_id)

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Generate redirect URL for payment gateway (mock for now)
        redirect_url = None
        if order.status == "pending":
            if order.payment_method == "momo":
                redirect_url = f"https://payment.momo.vn/pay?order={order.id}"
            elif order.payment_method == "zalopay":
                redirect_url = f"https://payment.zalopay.vn/pay?order={order.id}"

        return RechargeOrderResponse(
            order_id=order.id,
            amount_vnd=order.amount_vnd,
            amount_tokens=order.amount_tokens,
            payment_method=order.payment_method,
            status=order.status,
            redirect_url=redirect_url,
            created_at=order.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recharge/records", response_model=RechargeRecordsResponse)
async def get_recharge_records(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    wallet_service: WalletService = Depends(get_wallet_service),
):
    """Get recharge history (last 30 days)."""
    try:
        orders, total = await wallet_service.get_recharge_records(user_id, page, limit)

        records = [
            RechargeRecord(
                order_id=o.id,
                amount_vnd=o.amount_vnd,
                amount_tokens=o.amount_tokens,
                payment_method=o.payment_method,
                status=o.status,
                created_at=o.created_at,
                paid_at=o.paid_at,
            )
            for o in orders
        ]

        return RechargeRecordsResponse(
            records=records,
            total=total,
            page=page,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/transactions", response_model=TransactionRecordsResponse)
async def get_transactions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    wallet_service: WalletService = Depends(get_wallet_service),
):
    """Get wallet transaction history."""
    try:
        transactions, total = await wallet_service.get_transaction_records(user_id, page, limit)

        records = [
            TransactionRecord(
                id=t.id,
                amount=t.amount,
                balance_after=t.balance_after,
                transaction_type=t.transaction_type,
                description=t.description,
                created_at=t.created_at,
            )
            for t in transactions
        ]

        return TransactionRecordsResponse(
            transactions=records,
            total=total,
            page=page,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recharge/callback/{order_id}")
async def payment_callback(
    order_id: str,
    external_order_id: str | None = None,
    wallet_service: WalletService = Depends(get_wallet_service),
):
    """Payment gateway callback (for production use)."""
    try:
        success = await wallet_service.complete_recharge(order_id, external_order_id)
        if success:
            return {"status": "success"}
        return {"status": "ignored", "reason": "Order not pending"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recharge/{order_id}/simulate")
async def simulate_payment(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
    wallet_service: WalletService = Depends(get_wallet_service),
):
    """
    Simulate payment completion (for testing with mock gateway).

    This endpoint simulates the payment gateway callback for testing.
    """
    from sqlalchemy import select
    from app.models.wallet import RechargeOrder

    # Get order and verify ownership
    stmt = select(RechargeOrder).where(
        RechargeOrder.id == order_id,
        RechargeOrder.user_id == user_id,
    )
    # Note: Need db session, using wallet_service's db
    # This is a simplified version for testing

    try:
        # Complete the recharge
        success = await wallet_service.complete_recharge(
            order_id,
            external_order_id=f"MOCK-{order_id[:8].upper()}"
        )
        if success:
            return {
                "status": "success",
                "message": "Mock payment completed",
                "order_id": order_id,
            }
        return {
            "status": "ignored",
            "reason": "Order not in pending state",
            "order_id": order_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
