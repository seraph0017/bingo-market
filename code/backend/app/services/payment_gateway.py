"""Payment Gateway Service for MoMo/ZaloPay integration."""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import httpx

from app.core.config import settings


class PaymentMethod(str, Enum):
    """Payment method enum."""
    MOMO = "momo"
    ZALOPAY = "zalopay"
    BANK_TRANSFER = "bank_transfer"


class PaymentStatus(str, Enum):
    """Payment status enum."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PaymentRequest:
    """Payment request data."""
    order_id: str
    user_id: str
    user_name: str
    user_phone: str
    amount: int  # In VND
    currency: str = "VND"
    description: str = "Nạp tiền vào Bingo Market"


@dataclass
class PaymentResponse:
    """Payment response data."""
    order_id: str
    payment_url: str
    qr_code: Optional[str] = None
    external_order_id: Optional[str] = None
    status: str = PaymentStatus.PENDING


@dataclass
class PaymentCallbackData:
    """Payment callback data."""
    order_id: str
    external_order_id: str
    amount: int
    status: str
    signature: str
    timestamp: int


class PaymentGatewayService:
    """
    Payment Gateway Service for MoMo/ZaloPay integration.

    This service handles:
    - Payment initiation with MoMo/ZaloPay
    - Payment status checking
    - Callback verification
    - Refund processing (future)
    """

    def __init__(self):
        # MoMo configuration
        self.momo_access_key = settings.momo_access_key
        self.momo_secret_key = settings.momo_secret_key
        self.momo_partner_code = settings.momo_partner_code
        self.momo_end_point = "https://test-payment.momo.vn/v2/gateway/api"

        # ZaloPay configuration
        self.zalopay_app_id = settings.zalopay_app_id
        self.zalopay_key_1 = settings.zalopay_key_1
        self.zalopay_key_2 = settings.zalopay_key_2
        self.zalopay_end_point = "https://sandbox-openapi.zalopay.vn/v2/create"

        # Timeout settings
        self.timeout = 30  # seconds

        # Test mode flag (default to True if no API keys configured)
        self.test_mode = not all([
            self.momo_access_key,
            self.momo_secret_key,
            self.momo_partner_code,
        ])

    async def initiate_payment(
        self,
        request: PaymentRequest,
        payment_method: PaymentMethod,
    ) -> PaymentResponse:
        """
        Initiate payment with payment gateway.

        Args:
            request: Payment request data
            payment_method: Payment method (MoMo/ZaloPay)

        Returns:
            PaymentResponse with payment URL and QR code
        """
        if payment_method == PaymentMethod.MOMO:
            return await self._initiate_momo_payment(request)
        elif payment_method == PaymentMethod.ZALOPAY:
            return await self._initiate_zalopay_payment(request)
        else:
            raise ValueError(f"Unsupported payment method: {payment_method}")

    async def _initiate_momo_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Initiate MoMo payment."""
        # Generate MoMo signature
        timestamp = int(time.time() * 1000)
        order_info = f"testpartner{request.order_id}"

        # Signature = HMAC(SHA256, SecretKey, accessKey + orderId + amount + orderInfo)
        signature_data = f"{self.momo_access_key}{request.order_id}{request.amount}{order_info}"
        signature = hmac.new(
            self.momo_secret_key.encode(),
            signature_data.encode(),
            hashlib.sha256
        ).hexdigest()

        # Prepare request body
        payload = {
            "partnerCode": self.momo_partner_code,
            "accessKey": self.momo_access_key,
            "requestId": request.order_id,
            "amount": str(request.amount),
            "orderId": order_info,
            "orderInfo": request.description,
            "redirectUrl": f"https://bingomarket.io/payment/callback/momo?order_id={request.order_id}",
            "ipnUrl": f"https://api.bingomarket.io/api/v1/wallet/recharge/callback/{request.order_id}",
            "extraData": request.user_id,
            "requestType": "captureWallet",
            "signature": signature,
        }

        if self.test_mode:
            # In test mode, return mock payment URL
            return PaymentResponse(
                order_id=request.order_id,
                payment_url=f"https://test-payment.momo.vn/v2/gateway/api/pay?order={request.order_id}",
                qr_code=f"MOMO-QR-{request.order_id[:8].upper()}",
                status=PaymentStatus.PENDING,
            )

        # In production, call actual MoMo API
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.momo_end_point}/create",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()

            return PaymentResponse(
                order_id=request.order_id,
                payment_url=result.get("payUrl", ""),
                qr_code=result.get("qrCodeUrl", ""),
                external_order_id=result.get("orderId", ""),
                status=PaymentStatus.PENDING,
            )

    async def _initiate_zalopay_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Initiate ZaloPay payment."""
        # Generate ZaloPay signature
        timestamp = int(time.time() * 1000)
        order_info = f"zalopay{request.order_id}"

        # Generate MAC (Message Authentication Code)
        data = f"{self.zalopay_app_id}|{request.order_id}|{request.user_id}|{request.description}|{request.amount}|{timestamp}"
        signature = hmac.new(
            self.zalopay_key_1.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

        # Prepare request body
        payload = {
            "app_id": self.zalopay_app_id,
            "app_trans_id": request.order_id,
            "app_user": request.user_id,
            "app_time": timestamp,
            "amount": request.amount,
            "description": request.description,
            "bank_code": "",
            "callback_url": f"https://api.bingomarket.io/api/v1/wallet/recharge/callback/{request.order_id}",
            "return_url": f"https://bingomarket.io/payment/callback/zalopay?order_id={request.order_id}",
            "mac": signature,
        }

        if self.test_mode:
            # In test mode, return mock payment URL
            return PaymentResponse(
                order_id=request.order_id,
                payment_url=f"https://sandbox-openapi.zalopay.vn/v2/create?order={request.order_id}",
                qr_code=f"ZALOPAY-QR-{request.order_id[:8].upper()}",
                status=PaymentStatus.PENDING,
            )

        # In production, call actual ZaloPay API
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                self.zalopay_end_point,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            result = response.json()

            return PaymentResponse(
                order_id=request.order_id,
                payment_url=result.get("order_url", ""),
                qr_code=result.get("qr_code", ""),
                external_order_id=result.get("zp_trans_id", ""),
                status=PaymentStatus.PENDING,
            )

    async def verify_callback(
        self,
        payment_method: PaymentMethod,
        callback_data: PaymentCallbackData,
    ) -> bool:
        """
        Verify payment gateway callback signature.

        Args:
            payment_method: Payment method
            callback_data: Callback data from payment gateway

        Returns:
            True if signature is valid, False otherwise
        """
        if payment_method == PaymentMethod.MOMO:
            return self._verify_momo_callback(callback_data)
        elif payment_method == PaymentMethod.ZALOPAY:
            return self._verify_zalopay_callback(callback_data)
        return False

    def _verify_momo_callback(self, callback_data: PaymentCallbackData) -> bool:
        """Verify MoMo callback signature."""
        # MoMo callback format:
        # orderId|amount|orderInfo|message|requestId|responseTime|errorCode|localMessage
        signature_data = f"{callback_data.order_id}|{callback_data.amount}|"
        expected_signature = hmac.new(
            self.momo_secret_key.encode(),
            signature_data.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, callback_data.signature)

    def _verify_zalopay_callback(self, callback_data: PaymentCallbackData) -> bool:
        """Verify ZaloPay callback signature."""
        # ZaloPay callback format
        data = f"{self.zalopay_app_id}|{callback_data.external_order_id}|{callback_data.amount}"
        expected_signature = hmac.new(
            self.zalopay_key_1.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, callback_data.signature)

    async def check_payment_status(
        self,
        order_id: str,
        payment_method: PaymentMethod,
    ) -> str:
        """
        Check payment status with payment gateway.

        Args:
            order_id: Order ID
            payment_method: Payment method

        Returns:
            Payment status (pending/success/failed/cancelled)
        """
        if payment_method == PaymentMethod.MOMO:
            return await self._check_momo_status(order_id)
        elif payment_method == PaymentMethod.ZALOPAY:
            return await self._check_zalopay_status(order_id)
        return PaymentStatus.FAILED

    async def _check_momo_status(self, order_id: str) -> str:
        """Check MoMo payment status."""
        timestamp = int(time.time() * 1000)
        order_info = f"testpartner{order_id}"

        # Generate signature for query
        signature_data = f"{self.momo_access_key}{order_id}{order_info}"
        signature = hmac.new(
            self.momo_secret_key.encode(),
            signature_data.encode(),
            hashlib.sha256
        ).hexdigest()

        payload = {
            "partnerCode": self.momo_partner_code,
            "accessKey": self.momo_access_key,
            "requestId": order_id,
            "orderId": order_info,
            "signature": signature,
            "lang": "vi",
        }

        if self.test_mode:
            return PaymentStatus.PENDING

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.momo_end_point}/query",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            result = response.json()

            # Map MoMo status to our status
            status_map = {
                "SUCCESS": PaymentStatus.SUCCESS,
                "PENDING": PaymentStatus.PENDING,
                "FAILED": PaymentStatus.FAILED,
                "CANCELLED": PaymentStatus.CANCELLED,
            }
            return status_map.get(result.get("status", ""), PaymentStatus.FAILED)

    async def _check_zalopay_status(self, order_id: str) -> str:
        """Check ZaloPay payment status."""
        timestamp = int(time.time() * 1000)

        # Generate signature
        data = f"{self.zalopay_app_id}|{order_id}|1"
        signature = hmac.new(
            self.zalopay_key_1.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

        payload = {
            "app_id": self.zalopay_app_id,
            "app_trans_id": order_id,
            "mac": signature,
        }

        if self.test_mode:
            return PaymentStatus.PENDING

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                "https://sandbox-openapi.zalopay.vn/v2/query",
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            result = response.json()

            # Map ZaloPay status to our status
            status_map = {
                1: PaymentStatus.SUCCESS,  # Processing
                2: PaymentStatus.SUCCESS,  # Success
                -1: PaymentStatus.FAILED,  # Failed
                -2: PaymentStatus.CANCELLED,  # Cancelled
            }
            return status_map.get(result.get("status", -1), PaymentStatus.FAILED)


# Global payment gateway service instance
payment_gateway_service = PaymentGatewayService()
