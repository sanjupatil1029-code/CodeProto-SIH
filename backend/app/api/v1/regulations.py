import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth import User, UserRole
from app.schemas.regulatory_update import (
    RegulatoryUpdateCreateSchema,
    RegulatoryUpdateReviewSchema,
    RegulatoryUpdateOut,
    RuleVersionHistoryOut,
)
from app.services.auth_service import get_current_user
from app.services.regulatory_update_service import RegulatoryUpdateService

router = APIRouter(prefix="/regulations", tags=["Regulatory Update Engine"])


@router.post("/updates/propose", response_model=RegulatoryUpdateOut)
async def propose_regulatory_update(
    schema: RegulatoryUpdateCreateSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 15: Propose a new draft regulatory update from official government notification/gazette.
    Stores AI-extracted rule diff comparisons and impact analysis.
    """
    return await RegulatoryUpdateService.propose_regulatory_update(db=db, schema=schema)


@router.get("/updates/pending", response_model=List[RegulatoryUpdateOut])
async def get_pending_regulatory_updates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 15: List draft regulatory updates pending Admin review.
    """
    return await RegulatoryUpdateService.get_pending_updates(db=db)


@router.post("/updates/{update_id}/review", response_model=RegulatoryUpdateOut)
async def review_regulatory_update(
    update_id: uuid.UUID,
    schema: RegulatoryUpdateReviewSchema,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 15: Admin review approval pipeline.
    Approving creates a NEW ApprovalRule version (Version 2.0), supersedes old version,
    and re-evaluates active business roadmaps without overwriting history.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.OFFICER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admins or Officers can review and approve regulatory updates"
        )
    return await RegulatoryUpdateService.review_regulatory_update(
        db=db,
        update_id=update_id,
        approve=schema.approve,
        admin_user_id=current_user.id,
        review_notes=schema.review_notes
    )


@router.get("/history/{rule_code}", response_model=RuleVersionHistoryOut)
async def get_rule_version_history(
    rule_code: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 15: Retrieve full immutable version history and audit log for an approval rule (e.g. FSSAI_LICENSE).
    """
    return await RegulatoryUpdateService.get_rule_version_history(db=db, rule_code=rule_code)
