"""Device management service."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.device import LoginDevice
from app.models.user import User


class DeviceService:
    """Device management service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _parse_user_agent(self, user_agent: str | None) -> dict:
        """Parse user agent string to extract device info."""
        if not user_agent:
            return {"device_type": "unknown", "os": "unknown", "browser": "unknown"}

        ua = user_agent.lower()

        # Detect device type
        if "mobile" in ua or "android" in ua and "mobile" in ua:
            device_type = "mobile"
        elif "tablet" in ua or "ipad" in ua:
            device_type = "tablet"
        else:
            device_type = "desktop"

        # Detect OS
        os = "unknown"
        if "windows" in ua:
            os = "Windows"
        elif "mac os" in ua or "macos" in ua:
            os = "macOS"
        elif "linux" in ua:
            os = "Linux"
        elif "iphone" in ua or "ios" in ua:
            os = "iOS"
        elif "android" in ua:
            os = "Android"

        # Detect browser
        browser = "unknown"
        if "chrome" in ua and "edg" not in ua:
            browser = "Chrome"
        elif "firefox" in ua:
            browser = "Firefox"
        elif "safari" in ua and "chrome" not in ua:
            browser = "Safari"
        elif "edg" in ua:
            browser = "Edge"
        elif "msie" in ua or "trident" in ua:
            browser = "IE"

        return {"device_type": device_type, "os": os, "browser": browser}

    def _generate_fingerprint(self, user_agent: str | None, ip_address: str | None) -> str:
        """Generate device fingerprint."""
        import hashlib
        data = f"{user_agent or ''}:{ip_address or ''}"
        return hashlib.md5(data.encode()).hexdigest()[:16]

    async def add_device(
        self,
        user_id: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> LoginDevice:
        """Add or update login device."""
        # Parse user agent
        info = self._parse_user_agent(user_agent)
        fingerprint = self._generate_fingerprint(user_agent, ip_address)

        # Check if device exists
        stmt = select(LoginDevice).where(
            LoginDevice.device_fingerprint == fingerprint,
            LoginDevice.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        device = result.scalar_one_or_none()

        if device:
            # Update existing device
            device.is_current = True
            device.last_active_at = datetime.utcnow()
            device.ip_address = ip_address
        else:
            # Create new device
            device = LoginDevice(
                user_id=user_id,
                device_name=info.get("device_type", "Unknown"),
                device_type=info["device_type"],
                os=info["os"],
                browser=info["browser"],
                ip_address=ip_address,
                user_agent=user_agent,
                device_fingerprint=fingerprint,
                is_current=True,
                last_active_at=datetime.utcnow(),
            )
            self.db.add(device)

        await self.db.flush()
        return device

    async def get_user_devices(self, user_id: str) -> list[LoginDevice]:
        """Get all devices for a user."""
        stmt = select(LoginDevice).where(
            LoginDevice.user_id == user_id
        ).order_by(LoginDevice.last_active_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def remove_device(self, user_id: str, device_id: str) -> bool:
        """Remove a device."""
        stmt = select(LoginDevice).where(
            LoginDevice.id == device_id,
            LoginDevice.user_id == user_id,
        )
        result = await self.db.execute(stmt)
        device = result.scalar_one_or_none()

        if not device:
            return False

        await self.db.delete(device)
        await self.db.flush()
        return True

    async def remove_all_other_devices(
        self, user_id: str, keep_device_id: str | None = None
    ) -> int:
        """Remove all devices except current one."""
        stmt = select(LoginDevice).where(LoginDevice.user_id == user_id)
        if keep_device_id:
            stmt = stmt.where(LoginDevice.id != keep_device_id)
        result = await self.db.execute(stmt)
        devices = result.scalars().all()

        count = 0
        for device in devices:
            await self.db.delete(device)
            count += 1

        await self.db.flush()
        return count

    async def update_last_active(self, device_id: str) -> bool:
        """Update device last active time."""
        stmt = select(LoginDevice).where(LoginDevice.id == device_id)
        result = await self.db.execute(stmt)
        device = result.scalar_one_or_none()

        if not device:
            return False

        device.last_active_at = datetime.utcnow()
        await self.db.flush()
        return True
