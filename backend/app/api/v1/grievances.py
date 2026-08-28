import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth import User, UserRole
from app.schemas.grievance import (
    GrievanceCreateSchema,
    GrievanceAssignSchema,
    GrievanceResolveSchema,
    GrievanceOut,
)
from app.services.auth_service import get_current_user
from app.services.grievance_service import GrievanceService
from app.services.business_service import BusinessService

router = APIRouter(prefix="/grievances", tags=["Grievance & Escalation Engine"])


@router.post("/create", response_model=GrievanceOut)
async def create_grievance(
    schema: GrievanceCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 13: Raise a new grievance ticket for SLA delay, document query, or officer issue.
    Auto-assigns initial resolution deadline based on priority.
    """
    return await GrievanceService.create_grievance(
        db=db, complainant_id=current_user.id, schema=schema
    )


@router.get("/business/{business_id}", response_model=List[GrievanceOut])
async def get_business_grievances(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 13: Get all grievances and escalation statuses for a business profile.
    """
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    return await GrievanceService.get_business_grievances(db=db, business_id=business_id)


@router.post("/{grievance_id}/assign", response_model=GrievanceOut)
async def assign_grievance_officer(
    grievance_id: uuid.UUID,
    schema: GrievanceAssignSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 13: Assign a departmental officer to handle a grievance ticket.
    """
    return await GrievanceService.assign_officer(
        db=db, grievance_id=grievance_id, officer_id=schema.officer_id
    )


@router.post("/{grievance_id}/resolve", response_model=GrievanceOut)
async def resolve_grievance(
    grievance_id: uuid.UUID,
    schema: GrievanceResolveSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 13: Resolve a grievance ticket and record official resolution notes.
    """
    return await GrievanceService.resolve_grievance(
        db=db,
        grievance_id=grievance_id,
        resolution_notes=schema.resolution_notes,
        officer_id=current_user.id
    )


@router.post("/business/{business_id}/check-escalations", response_model=List[GrievanceOut])
async def check_and_escalate_grievances(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 13: Trigger automatic multi-tier escalation engine scan.
    Escalates tickets exceeding resolution deadline (Level 1 Nodal -> Level 2 Senior -> Level 3 Secretariat).
    """
    return await GrievanceService.check_and_escalate_grievances(db=db, business_id=business_id)
