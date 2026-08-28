import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.auth import User, UserRole
from app.schemas.business import BusinessCreate, BusinessUpdate, BusinessOut
from app.services.auth_service import get_current_user, RoleChecker
from app.services.business_service import BusinessService

router = APIRouter(prefix="/businesses", tags=["Business Profiles"])


@router.post("/", response_model=BusinessOut, status_code=status.HTTP_201_CREATED)
async def create_business(
    schema: BusinessCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new industrial/business profile.
    Only available to ENTREPRENEURs (or ADMINs).
    """
    if current_user.role not in [UserRole.ENTREPRENEUR, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only entrepreneurs can register business profiles"
        )
    return await BusinessService.create_business(db, current_user.id, schema)


@router.get("/", response_model=List[BusinessOut])
async def list_businesses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve registered business profiles.
    - Entrepreneurs: Retrieves their own business profiles.
    - Officers/Admins: Retrieves all registered business profiles.
    """
    if current_user.role in [UserRole.OFFICER, UserRole.ADMIN]:
        return await BusinessService.get_all_businesses(db)
    return await BusinessService.get_user_businesses(db, current_user.id)


@router.get("/{business_id}", response_model=BusinessOut)
async def get_business_details(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific business profile.
    Access restricted to the owner of the business, or an Officer/Admin.
    """
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )

    # Permission check: Owner, Officer, or Admin
    if (
        business.owner_id != current_user.id 
        and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this business profile"
        )
    
    return business


@router.put("/{business_id}", response_model=BusinessOut)
async def update_business(
    business_id: uuid.UUID,
    schema: BusinessUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update details of a business profile.
    Only the owner or an Admin can update.
    """
    return await BusinessService.update_business(
        db=db,
        business_id=business_id,
        user_id=current_user.id,
        role=current_user.role,
        schema=schema
    )


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a business profile.
    Only the owner or an Admin can delete.
    """
    await BusinessService.delete_business(
        db=db,
        business_id=business_id,
        user_id=current_user.id,
        role=current_user.role
    )
    return None
