"""SMS service for verification codes."""

import random
import string
from typing import Optional

from app.core.redis import get_redis


class SMSService:
    """SMS service for sending verification codes."""

    def __init__(self):
        self.redis = None

    async def _get_redis_client(self):
        """Get Redis client."""
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis

    def generate_code(self, length: int = 6) -> str:
        """Generate random verification code."""
        return "".join(random.choices(string.digits, k=length))

    async def send_verification_code(
        self, phone: str, code: Optional[str] = None, expire_seconds: int = 60
    ) -> bool:
        """
        Send verification code to phone number.

        In production, this would integrate with actual SMS providers like:
        - Twilio
        - Vonage
        - Local Vietnam SMS providers

        For now, it stores the code in Redis for testing.
        """
        if code is None:
            code = self.generate_code()

        try:
            redis_client = await self._get_redis_client()
            # Store code with expiry
            key = f"sms_code:{phone}"
            await redis_client.setex(key, expire_seconds, code)

            # TODO: Integrate with actual SMS provider
            # Example: await twilio_client.messages.create(...)
            print(f"[SMS] Sending code {code} to {phone}")

            return True
        except Exception as e:
            print(f"[SMS] Failed to send code: {e}")
            return False

    async def verify_code(self, phone: str, code: str) -> bool:
        """Verify SMS code."""
        try:
            redis_client = await self._get_redis_client()
            key = f"sms_code:{phone}"
            stored_code = await redis_client.get(key)

            if stored_code == code:
                # Delete code after successful verification
                await redis_client.delete(key)
                return True
            return False
        except Exception:
            return False

    async def get_rate_limit_key(self, phone: str) -> str:
        """Get rate limit key for phone."""
        return f"sms_rate_limit:{phone}"

    async def check_rate_limit(self, phone: str, max_requests: int = 5, window_seconds: int = 3600) -> bool:
        """
        Check if phone has exceeded rate limit.

        Default: 5 requests per hour
        """
        try:
            redis_client = await self._get_redis_client()
            key = await self.get_rate_limit_key(phone)

            count = await redis_client.get(key)
            if count is None:
                await redis_client.setex(key, window_seconds, "1")
                return True

            if int(count) >= max_requests:
                return False

            await redis_client.incr(key)
            return True
        except Exception:
            return True


# Global SMS service instance
sms_service = SMSService()
