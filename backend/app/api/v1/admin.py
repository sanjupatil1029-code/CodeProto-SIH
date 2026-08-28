import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth import User, UserRole
from app.schemas.audit import AuditLogQueryResponse
from app.services.auth_service import get_current_user
from app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Admin & Audit Logs"])


@router.get("/audit-logs", response_model=AuditLogQueryResponse)
async def query_audit_logs(
    resource_type: Optional[str] = Query(None, description="Filter by resource type (e.g. BusinessApproval, Document, ApprovalRule)"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    actor_id: Optional[uuid.UUID] = Query(None, description="Filter by actor user ID"),
    action: Optional[str] = Query(None, description="Filter by action name (e.g. APPROVAL_STATUS_CHANGED, RULE_VERSION_APPROVED)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 17: Query immutable append-only audit trail records.
    Restricted to Admins and Nodal Officers.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.OFFICER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to Admins or Officers"
        )
    return await AuditService.get_audit_logs(
        db=db,
        resource_type=resource_type,
        resource_id=resource_id,
        actor_id=actor_id,
        action=action,
        limit=limit,
        offset=offset
    )


@router.get("/audit-logs/resource/{resource_type}/{resource_id}", response_model=AuditLogQueryResponse)
async def get_resource_audit_history(
    resource_type: str,
    resource_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 17: Retrieve complete statutory audit history for a specific resource.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.OFFICER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to Admins or Officers"
        )
    return await AuditService.get_audit_logs(
        db=db,
        resource_type=resource_type,
        resource_id=resource_id,
        limit=limit,
        offset=offset
    )
