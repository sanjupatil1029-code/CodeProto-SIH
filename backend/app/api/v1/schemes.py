import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth import User
from app.models.scheme import Scheme
from app.schemas.scheme import SchemeOut, BusinessSchemeMatchesResponse
from app.services.auth_service import get_current_user
from app.services.scheme_matcher_service import SchemeMatcherService
from app.services.business_service import BusinessService

router = APIRouter(prefix="/schemes", tags=["Government Scheme Matcher"])


@router.get("/business/{business_id}/matches", response_model=BusinessSchemeMatchesResponse)
async def get_business_scheme_matches(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 14: Evaluate business profile against government incentive schemes.
    Returns matched schemes, subsidy benefit estimates, explainability reasons, and document checklists.
    """
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    return await SchemeMatcherService.match_schemes_for_business(db=db, business_id=business_id)


@router.get("/list", response_model=List[SchemeOut])
async def list_government_schemes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Module 14: List all active government incentive schemes in the database.
    """
    await SchemeMatcherService.seed_default_schemes(db)
    res = await db.execute(select(Scheme).where(Scheme.is_active == True))
    return list(res.scalars().all())
