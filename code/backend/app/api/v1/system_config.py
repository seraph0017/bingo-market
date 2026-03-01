"""System configuration API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Any

from app.core.database import get_db
from app.core.security import verify_token
from app.services.system_config import SystemConfigService
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()


class ConfigResponse(BaseModel):
    """Configuration response."""

    config_key: str
    config_value: Any
    value_type: str
    description: str | None
    is_public: bool
    is_editable: bool


class ConfigCreateRequest(BaseModel):
    """Create configuration request."""

    config_key: str = Field(..., max_length=100)
    config_value: Any
    value_type: str = "string"
    description: str | None = None
    is_public: bool = False
    is_editable: bool = True


class ConfigUpdateRequest(BaseModel):
    """Update configuration request."""

    config_value: Any
    description: str | None = None
    is_public: bool | None = None


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current user ID from token."""
    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    return payload["sub"]


async def get_config_service(db: AsyncSession = Depends(get_db)) -> SystemConfigService:
    """Get config service dependency."""
    return SystemConfigService(db)


@router.get("/configs", response_model=list[ConfigResponse])
async def get_all_configs(
    config_service: SystemConfigService = Depends(get_config_service),
):
    """Get all configurations (admin only)."""
    # TODO: Add admin role check
    configs = await config_service.get_all_configs()
    return [ConfigResponse(**c) for c in configs]


@router.get("/configs/public", response_model=dict)
async def get_public_configs(
    config_service: SystemConfigService = Depends(get_config_service),
):
    """Get public configurations (accessible to all users)."""
    return await config_service.get_public_configs()


@router.get("/configs/{key}", response_model=ConfigResponse)
async def get_config(
    key: str,
    config_service: SystemConfigService = Depends(get_config_service),
):
    """Get configuration by key."""
    value = await config_service.get_config(key, use_cache=False)
    if value is None:
        raise HTTPException(status_code=404, detail="Config not found")

    # Get full config info
    configs = await config_service.get_all_configs()
    for c in configs:
        if c["config_key"] == key:
            return ConfigResponse(**c)

    raise HTTPException(status_code=404, detail="Config not found")


@router.post("/configs", response_model=ConfigResponse)
async def create_config(
    data: ConfigCreateRequest,
    user_id: str = Depends(get_current_user_id),
    config_service: SystemConfigService = Depends(get_config_service),
):
    """Create or update configuration (admin only)."""
    # TODO: Add admin role check
    config = await config_service.set_config(
        key=data.config_key,
        value=data.config_value,
        value_type=data.value_type,
        description=data.description,
        is_public=data.is_public,
        is_editable=data.is_editable,
    )
    return ConfigResponse(
        config_key=config.config_key,
        config_value=config_service._parse_value(config.config_value, config.value_type),
        value_type=config.value_type,
        description=config.description,
        is_public=config.is_public,
        is_editable=config.is_editable,
    )


@router.put("/configs/{key}", response_model=ConfigResponse)
async def update_config(
    key: str,
    data: ConfigUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    config_service: SystemConfigService = Depends(get_config_service),
):
    """Update configuration (admin only)."""
    # TODO: Add admin role check
    try:
        config = await config_service.set_config(
            key=key,
            value=data.config_value,
            description=data.description,
            is_public=data.is_public if data.is_public is not None else False,
        )
        return ConfigResponse(
            config_key=config.config_key,
            config_value=config_service._parse_value(config.config_value, config.value_type),
            value_type=config.value_type,
            description=config.description,
            is_public=config.is_public,
            is_editable=config.is_editable,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/configs/{key}")
async def delete_config(
    key: str,
    user_id: str = Depends(get_current_user_id),
    config_service: SystemConfigService = Depends(get_config_service),
):
    """Delete configuration (admin only)."""
    # TODO: Add admin role check
    try:
        success = await config_service.delete_config(key)
        if success:
            return {"status": "success", "message": "Config deleted"}
        raise HTTPException(status_code=404, detail="Config not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
