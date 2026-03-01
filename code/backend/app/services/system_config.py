"""System configuration service."""

from __future__ import annotations

import json
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.system_config import SystemConfig


class SystemConfigService:
    """System configuration service."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache: dict[str, Any] = {}

    async def get_config(self, key: str, use_cache: bool = True) -> Any | None:
        """Get configuration value by key."""
        # Try cache first
        if use_cache and key in self._cache:
            return self._cache[key]

        stmt = select(SystemConfig).where(SystemConfig.config_key == key)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            return None

        # Parse value based on type
        value = self._parse_value(config.config_value, config.value_type)
        self._cache[key] = value
        return value

    async def set_config(
        self,
        key: str,
        value: Any,
        value_type: str = "string",
        description: Optional[str] = None,
        is_public: bool = False,
        is_editable: bool = True,
    ) -> SystemConfig:
        """Set configuration value."""
        # Convert value to string
        config_value = self._serialize_value(value, value_type)

        # Check if config exists
        stmt = select(SystemConfig).where(SystemConfig.config_key == key)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()

        if config:
            if not config.is_editable:
                raise ValueError(f"Config '{key}' is not editable")
            config.config_value = config_value
            config.value_type = value_type
            config.description = description or config.description
            config.is_public = is_public or config.is_public
        else:
            config = SystemConfig(
                config_key=key,
                config_value=config_value,
                value_type=value_type,
                description=description,
                is_public=is_public,
                is_editable=is_editable,
            )
            self.db.add(config)

        # Invalidate cache
        self._cache.pop(key, None)

        await self.db.flush()
        return config

    async def get_public_configs(self) -> dict[str, Any]:
        """Get all public configurations."""
        stmt = select(SystemConfig).where(SystemConfig.is_public == True)
        result = await self.db.execute(stmt)
        configs = result.scalars().all()

        return {
            config.config_key: self._parse_value(config.config_value, config.value_type)
            for config in configs
        }

    async def delete_config(self, key: str) -> bool:
        """Delete configuration."""
        stmt = select(SystemConfig).where(SystemConfig.config_key == key)
        result = await self.db.execute(stmt)
        config = result.scalar_one_or_none()

        if not config:
            return False

        if not config.is_editable:
            raise ValueError(f"Config '{key}' is not deletable")

        await self.db.delete(config)
        self._cache.pop(key, None)
        await self.db.flush()
        return True

    def _parse_value(self, value: str, value_type: str) -> Any:
        """Parse string value to appropriate type."""
        if value_type == "json":
            return json.loads(value)
        elif value_type == "number":
            try:
                return int(value)
            except ValueError:
                return float(value)
        elif value_type == "boolean":
            return value.lower() in ("true", "1", "yes")
        else:
            return value

    def _serialize_value(self, value: Any, value_type: str) -> str:
        """Serialize value to string."""
        if value_type == "json":
            return json.dumps(value)
        elif value_type == "number":
            return str(value)
        elif value_type == "boolean":
            return "true" if value else "false"
        else:
            return str(value)

    async def get_all_configs(self) -> list[dict]:
        """Get all configurations."""
        stmt = select(SystemConfig).order_by(SystemConfig.config_key)
        result = await self.db.execute(stmt)
        configs = result.scalars().all()

        return [
            {
                "id": c.id,
                "config_key": c.config_key,
                "config_value": self._parse_value(c.config_value, c.value_type),
                "value_type": c.value_type,
                "description": c.description,
                "is_public": c.is_public,
                "is_editable": c.is_editable,
            }
            for c in configs
        ]
