import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth import User, UserRole
from app.schemas.workflows import BusinessApprovalOut, StatusUpdateSchema
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
    - Entrepreneurs: Can only update status from READY/NOT_STARTED -> IN_PROGRESS for their own business.
    - Officers/Admins: Can transition to any status.
    """
    return await WorkflowService.update_approval_status(
        db=db,
        approval_id=approval_id,
        user_id=current_user.id,
        role=current_user.role,
        target_status=schema.status
    )
