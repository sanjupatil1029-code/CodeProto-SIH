import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth import User, UserRole
from app.schemas.workflows import (
    BusinessApprovalOut,
    StatusUpdateSchema,
    WorkflowHandoffResponse,
    WorkflowSubmitResponse,
    AdapterStatusSyncResponse,
)
from app.adapters.factory import AdapterFactory
from app.services.auth_service import get_current_user
from app.services.workflow_service import WorkflowService
from app.services.business_service import BusinessService

router = APIRouter(prefix="/workflows", tags=["Workflows & Roadmap"])


@router.post("/roadmap/generate/{business_id}", response_model=List[BusinessApprovalOut])
async def generate_roadmap(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate or sync the approval roadmap for a business profile.
    Access restricted to the owner of the business or an Officer/Admin.
    """
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    
    if (
        business.owner_id != current_user.id 
        and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this business's roadmap"
        )

    return await WorkflowService.generate_roadmap(db, business_id)


@router.get("/roadmap/{business_id}", response_model=List[BusinessApprovalOut])
async def get_roadmap(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve the generated approval roadmap for a business.
    Access restricted to the owner of the business or an Officer/Admin.
    """
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    
    if (
        business.owner_id != current_user.id 
        and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this business's roadmap"
        )

    return await WorkflowService.get_roadmap(db, business_id)


@router.put("/approvals/{approval_id}/status", response_model=BusinessApprovalOut)
async def update_approval_status(
    approval_id: uuid.UUID,
    schema: StatusUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update status of a specific approval record in the roadmap.
    - Entrepreneurs: Can update status for their own business.
    - Officers/Admins: Can transition to any status.
    """
    return await WorkflowService.update_approval_status(
        db=db,
        approval_id=approval_id,
        user_id=current_user.id,
        role=current_user.role,
        target_status=schema.status
    )


@router.post("/approvals/{approval_id}/handoff", response_model=WorkflowHandoffResponse)
async def initiate_portal_handoff(
    approval_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 8 & 9: Initiate Official Government Portal Handoff.
    Marks status as OFFICIAL_PORTAL_HANDOFF and returns official portal URL (e.g., FoSCoS, GST, MAITRI).
    """
    return await WorkflowService.initiate_portal_handoff(
        db=db, approval_id=approval_id, user_id=current_user.id
    )


@router.post("/approvals/{approval_id}/submit", response_model=WorkflowSubmitResponse)
async def submit_application(
    approval_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 8 & 9: Submit application through Government Integration Adapter Layer.
    Generates external reference ID (e.g. FSSAI123456), calculates SLA deadline, and records internal workflow.
    """
    return await WorkflowService.submit_workflow_application(
        db=db, approval_id=approval_id, user_id=current_user.id
    )


@router.post("/approvals/{approval_id}/sync-status", response_model=AdapterStatusSyncResponse)
async def sync_external_status(
    approval_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 8 & 9: Sync application status from external government system / adapter.
    """
    return await WorkflowService.sync_external_status(
        db=db, approval_id=approval_id, user_id=current_user.id
    )


@router.get("/adapters/list", response_model=Dict[str, Any])
async def list_government_adapters():
    """
    Module 9: List registered Government Integration Adapters, their integration modes, and official portal URLs.
    """
    return AdapterFactory.list_registered_adapters()
