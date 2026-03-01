"""
Mock Payment Gateway Service.

This service simulates payment gateway behavior for testing purposes.
It mimics MoMo/ZaloPay payment flow without actual money transfer.

Usage:
    python scripts/mock_payment_gateway.py

API Endpoints:
    POST /mock/payment/initiate - Initiate payment
    POST /mock/payment/callback  - Simulate payment callback
    GET  /mock/payment/status/{order_id} - Check payment status
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import uuid

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uvicorn import run


app = FastAPI(title="Mock Payment Gateway", version="1.0.0")


# In-memory storage for mock payments
payments: Dict[str, dict] = {}


class InitiatePaymentRequest(BaseModel):
    """Initiate payment request."""
    order_id: str
    amount: int
    currency: str = "VND"
    user_id: str


class InitiatePaymentResponse(BaseModel):
    """Initiate payment response."""
    order_id: str
    payment_url: str
    qr_code: str | None = None


class PaymentCallbackRequest(BaseModel):
    """Payment callback request."""
    order_id: str
    status: str  # success, failed
    external_order_id: str | None = None


class PaymentStatusResponse(BaseModel):
    """Payment status response."""
    order_id: str
    status: str
    amount: int
    created_at: str
    paid_at: str | None = None


@app.post("/mock/payment/initiate", response_model=InitiatePaymentResponse)
async def initiate_payment(request: InitiatePaymentRequest):
    """
    Initiate a mock payment.

    This simulates creating a payment request with MoMo/ZaloPay.
    """
    payment_id = str(uuid.uuid4())

    payment = {
        "payment_id": payment_id,
        "order_id": request.order_id,
        "amount": request.amount,
        "currency": request.currency,
        "user_id": request.user_id,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
        "paid_at": None,
        "external_order_id": None,
    }

    payments[payment_id] = payment

    # Generate mock payment URL
    payment_url = f"http://localhost:8001/mock/payment/{payment_id}/pay"

    return InitiatePaymentResponse(
        order_id=request.order_id,
        payment_url=payment_url,
        qr_code=f"MOMO-QR-{payment_id[:8].upper()}",
    )


@app.get("/mock/payment/{payment_id}/pay")
async def mock_payment_page(payment_id: str):
    """
    Mock payment page.

    In real scenario, this would be the payment gateway's payment page.
    Here we just simulate successful payment after a delay.
    """
    if payment_id not in payments:
        raise HTTPException(status_code=404, detail="Payment not found")

    payment = payments[payment_id]

    # Simulate payment processing
    payment["status"] = "success"
    payment["paid_at"] = datetime.utcnow().isoformat()
    payment["external_order_id"] = f"MOCK-{uuid.uuid4().hex[:12].upper()}"

    return {
        "status": "success",
        "message": "Payment completed successfully",
        "order_id": payment["order_id"],
        "amount": payment["amount"],
        "external_order_id": payment["external_order_id"],
    }


@app.post("/mock/payment/callback")
async def simulate_callback(request: PaymentCallbackRequest):
    """
    Simulate payment gateway callback.

    This simulates the async callback from payment gateway.
    """
    # Find payment by order_id
    payment = None
    for p in payments.values():
        if p["order_id"] == request.order_id:
            payment = p
            break

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Update payment status
    payment["status"] = request.status
    if request.status == "success":
        payment["paid_at"] = datetime.utcnow().isoformat()
    if request.external_order_id:
        payment["external_order_id"] = request.external_order_id

    return {
        "status": "received",
        "order_id": request.order_id,
        "payment_status": payment["status"],
    }


@app.get("/mock/payment/status/{order_id}", response_model=PaymentStatusResponse)
async def get_payment_status(order_id: str):
    """Get payment status by order ID."""
    # Find payment by order_id
    payment = None
    for p in payments.values():
        if p["order_id"] == order_id:
            payment = p
            break

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return PaymentStatusResponse(
        order_id=payment["order_id"],
        status=payment["status"],
        amount=payment["amount"],
        created_at=payment["created_at"],
        paid_at=payment["paid_at"],
    )


@app.get("/mock/payment/list")
async def list_payments():
    """List all mock payments."""
    return {
        "payments": list(payments.values()),
        "total": len(payments),
    }


@app.post("/mock/payment/reset")
async def reset_payments():
    """Reset all mock payments (for testing)."""
    payments.clear()
    return {"status": "ok", "message": "All payments reset"}


# CLI runner
if __name__ == "__main__":
    print("=" * 60)
    print("MOCK PAYMENT GATEWAY SERVICE")
    print("=" * 60)
    print("\nThis service simulates MoMo/ZaloPay payment gateway.")
    print("\nEndpoints:")
    print("  POST /mock/payment/initiate  - Create payment")
    print("  GET  /mock/payment/{id}/pay  - Simulate payment")
    print("  POST /mock/payment/callback  - Simulate callback")
    print("  GET  /mock/payment/status/{order_id} - Check status")
    print("  GET  /mock/payment/list      - List all payments")
    print("  POST /mock/payment/reset     - Reset payments")
    print("\nStarting server on http://localhost:8001")
    print("=" * 60)

    run(app, host="0.0.0.0", port=8001)
