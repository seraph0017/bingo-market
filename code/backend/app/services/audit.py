"""Audit log service."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.models.audit import AuditLog


class AuditService:
    """Audit logging service."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        method: Optional[str] = None,
        endpoint: Optional[str] = None,
        request_body: Optional[dict] = None,
        response_status: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> AuditLog:
        """Log an action to the audit trail."""
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            method=method,
            endpoint=endpoint,
            request_body=json.dumps(request_body) if request_body else None,
            response_status=response_status,
            status=status,
            error_message=error_message,
            user_agent=user_agent,
            ip_address=ip_address,
            metadata_json=json.dumps(metadata) if metadata else None,
        )

        self.db.add(audit_log)
        await self.db.flush()
        await self.db.refresh(audit_log)

        return audit_log

    async def get_audit_logs(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Get audit logs with filters."""
        # Build query
        stmt = select(AuditLog)

        # Apply filters
        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if resource_type:
            stmt = stmt.where(AuditLog.resource_type == resource_type)
        if start_date:
            stmt = stmt.where(AuditLog.created_at >= start_date)
        if end_date:
            stmt = stmt.where(AuditLog.created_at <= end_date)

        # Get total count
        count_stmt = select(AuditLog).select_from(stmt.subquery())
        total = await self.db.execute(count_stmt)
        total_count = total.scalar() or 0

        # Order by created_at desc and apply pagination
        stmt = stmt.order_by(desc(AuditLog.created_at))
        stmt = stmt.offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        return list(logs), total_count

    async def log_login(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a login attempt."""
        await self.log_action(
            action="LOGIN",
            user_id=user_id,
            resource_type="USER",
            resource_id=user_id,
            status="success" if success else "failure",
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_logout(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """Log a logout."""
        await self.log_action(
            action="LOGOUT",
            user_id=user_id,
            resource_type="USER",
            resource_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    async def log_password_change(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a password change attempt."""
        await self.log_action(
            action="CHANGE_PASSWORD",
            user_id=user_id,
            resource_type="USER",
            resource_id=user_id,
            status="success" if success else "failure",
            error_message=error_message,
            ip_address=ip_address,
        )

    async def log_recharge(
        self,
        user_id: str,
        order_id: str,
        amount: int,
        success: bool,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log a recharge attempt."""
        await self.log_action(
            action="RECHARGE",
            user_id=user_id,
            resource_type="WALLET",
            resource_id=order_id,
            status="success" if success else "failure",
            metadata={"order_id": order_id, "amount": amount},
            ip_address=ip_address,
        )

    async def log_trade(
        self,
        user_id: str,
        topic_id: str,
        trade_type: str,
        amount: int,
        success: bool,
        ip_address: Optional[str] = None,
    ) -> None:
        """Log a trade attempt."""
        await self.log_action(
            action="TRADE",
            user_id=user_id,
            resource_type="TOPIC",
            resource_id=topic_id,
            status="success" if success else "failure",
            metadata={"trade_type": trade_type, "amount": amount},
            ip_address=ip_address,
        )
