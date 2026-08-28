import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth import User, UserRole
from app.schemas.rules import ApprovalRuleCreate, ApprovalRuleOut, RuleEvaluationResult
from app.services.auth_service import get_current_user, RoleChecker
from app.services.rule_engine_service import RuleEngineService
from app.services.business_service import BusinessService

router = APIRouter(prefix="/approvals", tags=["Regulatory Rules & Approvals"])


@router.post("/rules", response_model=ApprovalRuleOut, status_code=status.HTTP_201_CREATED)
async def create_rule(
    schema: ApprovalRuleCreate,
    current_user: User = Depends(RoleChecker([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Define a new regulatory approval rule.
    Only available to ADMINs.
    If the rule code already exists, the existing rule will be marked as SUPERSEDED and a new version is created.
    """
    try:
        return await RuleEngineService.create_rule(db, schema)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create rule: {str(e)}"
        )


@router.get("/rules", response_model=List[ApprovalRuleOut])
async def list_rules(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all active regulatory rules.
    Available to all authenticated users.
    """
    return await RuleEngineService.get_all_rules(db)


@router.get("/evaluate/{business_id}", response_model=List[RuleEvaluationResult])
async def evaluate_business_approvals(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Run the Rule Engine against a specific business profile.
    Access restricted to the owner of the business or an Officer/Admin.
    """
    # Check if business exists and verify ownership/permissions
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
            detail="You do not have permission to access or evaluate this business profile"
        )

    return await RuleEngineService.evaluate_business_approvals(db, business_id)
