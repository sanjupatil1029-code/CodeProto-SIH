import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth import User, UserRole
from app.schemas.inspection import (
    InspectionScheduleSchema,
    InspectionRescheduleSchema,
    InspectionReportSchema,
    InspectionOut,
)
from app.services.auth_service import get_current_user
from app.services.inspection_service import InspectionService
from app.services.business_service import BusinessService

router = APIRouter(prefix="/inspections", tags=["Inspection Management"])


@router.post("/schedule", response_model=InspectionOut)
async def schedule_inspection(
    schema: InspectionScheduleSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 12: Schedule a new statutory inspection for an approval.
    """
    return await InspectionService.schedule_inspection(db=db, schema=schema)


@router.get("/business/{business_id}", response_model=List[InspectionOut])
async def get_business_inspections(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 12: Get all inspections scheduled or completed for a business profile.
    """
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    return await InspectionService.get_business_inspections(db=db, business_id=business_id)


@router.post("/{inspection_id}/reschedule", response_model=InspectionOut)
async def reschedule_inspection(
    inspection_id: uuid.UUID,
    schema: InspectionRescheduleSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 12: Reschedule an inspection date and log rescheduling reason.
    """
    return await InspectionService.reschedule_inspection(
        db=db, inspection_id=inspection_id, schema=schema
    )


@router.post("/{inspection_id}/report", response_model=InspectionOut)
async def submit_inspection_report(
    inspection_id: uuid.UUID,
    schema: InspectionReportSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 12: Submit officer inspection findings report and complete/fail the inspection.
    Completing an inspection auto-approves the associated statutory license.
    """
    return await InspectionService.submit_inspection_report(
        db=db, inspection_id=inspection_id, schema=schema
    )
