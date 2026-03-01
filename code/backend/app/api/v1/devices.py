"""Device management API routes."""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import get_db
from app.core.security import verify_token
from app.services.device import DeviceService
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


async def get_device_service(db: AsyncSession = Depends(get_db)) -> DeviceService:
    """Get device service dependency."""
    return DeviceService(db)


@router.get("/devices")
async def get_devices(
    user_id: str = Depends(get_current_user_id),
    device_service: DeviceService = Depends(get_device_service),
):
    """Get user's login devices."""
    try:
        devices = await device_service.get_user_devices(user_id)

        return {
            "devices": [
                {
                    "id": d.id,
                    "device_name": d.device_name,
                    "device_type": d.device_type,
                    "os": d.os,
                    "browser": d.browser,
                    "ip_address": d.ip_address[:7] + "****" if d.ip_address else None,
                    "is_current": d.is_current,
                    "last_active_at": d.last_active_at.isoformat() if d.last_active_at else None,
                    "created_at": d.created_at.isoformat() if d.created_at else None,
                }
                for d in devices
            ],
            "total": len(devices),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/devices/{device_id}")
async def remove_device(
    device_id: str,
    user_id: str = Depends(get_current_user_id),
    device_service: DeviceService = Depends(get_device_service),
):
    """Remove a login device."""
    try:
        success = await device_service.remove_device(user_id, device_id)
        if success:
            return {"status": "success", "message": "Device removed"}
        raise HTTPException(status_code=404, detail="Device not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/devices/logout-all")
async def logout_all_devices(
    user_id: str = Depends(get_current_user_id),
    device_service: DeviceService = Depends(get_device_service),
):
    """Logout from all other devices."""
    try:
        count = await device_service.remove_all_other_devices(user_id)
        return {
            "status": "success",
            "message": f"Logged out from {count} devices",
            "devices_removed": count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
