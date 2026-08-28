import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogOut, AuditLogQueryResponse
from app.core.logging import logger


class AuditService:
    """
    Module 17: Immutable Append-Only Audit Log Service.
    Appends audit log records for all statutory actions, state changes, document validations,
    and officer reviews with complete old vs new JSON diffs.
    """

    @classmethod
    async def log_audit_event(
        cls,
        db: AsyncSession,
        action: str,
        resource_type: str,
        resource_id: str,
        actor_id: Optional[uuid.UUID] = None,
        actor_role: str = "SYSTEM",
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """
        Append an immutable audit log record.
        Strictly append-only: records are never overwritten or updated.
        """
        audit_entry = AuditLog(
            actor_id=actor_id,
            actor_role=actor_role,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            old_value=old_value or {},
            new_value=new_value or {},
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            request_id=request_id
        )

        db.add(audit_entry)
        await db.commit()
        await db.refresh(audit_entry)
        logger.info(f"[AUDIT LOG ENTRY] Action: '{action}' | Resource: {resource_type}:{resource_id} | Actor: {actor_role} ({actor_id or 'SYSTEM'})")
        return audit_entry

    @classmethod
    async def get_audit_logs(
        cls,
        db: AsyncSession,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        actor_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> AuditLogQueryResponse:
        """Query append-only audit trail records with filtering and pagination."""
        query = select(AuditLog)
        
        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.where(AuditLog.resource_id == str(resource_id))
        if actor_id:
            query = query.where(AuditLog.actor_id == actor_id)
        if action:
            query = query.where(AuditLog.action == action)

        query = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit)
        res = await db.execute(query)
        logs = list(res.scalars().all())

        # Total count query
        count_query = select(func.count(AuditLog.audit_id))
        if resource_type:
            count_query = count_query.where(AuditLog.resource_type == resource_type)
        if resource_id:
            count_query = count_query.where(AuditLog.resource_id == str(resource_id))
        if actor_id:
            count_query = count_query.where(AuditLog.actor_id == actor_id)
        if action:
            count_query = count_query.where(AuditLog.action == action)

        total_res = await db.execute(count_query)
        total_count = total_res.scalar() or 0

        items = [AuditLogOut.model_validate(log) for log in logs]

        return AuditLogQueryResponse(
            total_count=total_count,
            limit=limit,
            offset=offset,
            logs=items
        )
