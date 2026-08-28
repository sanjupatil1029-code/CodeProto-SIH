import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth import User, UserRole
from app.schemas.compliance import (
    CertificateDatesUpdate,
    ComplianceDashboardOut,
    SLABottleneckAnalyticsOut,
)
from app.schemas.workflows import BusinessApprovalOut
from app.services.auth_service import get_current_user
from app.services.business_service import BusinessService
from app.services.compliance_service import ComplianceService
from app.services.sla_engine_service import SLAEngineService

router = APIRouter(prefix="/compliance", tags=["Compliance & SLA Engine"])


@router.get("/business/{business_id}/renewals", response_model=ComplianceDashboardOut)
async def get_business_compliance_renewals(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 10: Get compliance & renewal dashboard report for a business profile.
    Checks 90d, 60d, 30d, 15d, 7d, 1d expiration reminder thresholds.
    """
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    return await ComplianceService.evaluate_business_renewals(db, business_id)


@router.post("/business/{business_id}/check-renewals", response_model=ComplianceDashboardOut)
async def trigger_business_renewals_check(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 10: Manually trigger batch evaluation of all approval expiration dates & renewal thresholds.
    """
    return await ComplianceService.evaluate_business_renewals(db, business_id)


@router.put("/approvals/{approval_id}/dates", response_model=BusinessApprovalOut)
async def update_certificate_dates(
    approval_id: uuid.UUID,
    schema: CertificateDatesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 10: Assign or update official certificate issue & expiry dates.
    Auto-calculates renewal start date and deadline.
    """
    return await ComplianceService.update_certificate_dates(
        db=db, approval_id=approval_id, schema=schema
    )


@router.get("/business/{business_id}/sla-bottlenecks", response_model=SLABottleneckAnalyticsOut)
async def get_business_sla_bottlenecks(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 11: Get SLA breach warnings (>=80%), SLA breaches (>=100%), and department bottleneck analytics.
    """
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    return await SLAEngineService.evaluate_business_slas(db, business_id)


@router.post("/business/{business_id}/evaluate-sla", response_model=SLABottleneckAnalyticsOut)
async def evaluate_business_slas(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 11: Trigger batch SLA evaluation and update bottleneck risk levels across authorities.
    """
    return await SLAEngineService.evaluate_business_slas(db, business_id)
