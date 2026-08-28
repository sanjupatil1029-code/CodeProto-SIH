import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.business import Business
from app.models.auth import UserRole
from app.schemas.business import BusinessCreate, BusinessUpdate
from app.core.logging import logger


class BusinessService:
    @staticmethod
    async def get_business_by_id(db: AsyncSession, business_id: uuid.UUID) -> Optional[Business]:
        """Fetch a business profile by its ID."""
        result = await db.execute(select(Business).where(Business.id == business_id))
        return result.scalars().first()

    @staticmethod
    async def get_user_businesses(db: AsyncSession, owner_id: uuid.UUID) -> List[Business]:
        """Retrieve all business profiles registered by a specific entrepreneur."""
        result = await db.execute(select(Business).where(Business.owner_id == owner_id))
        return list(result.scalars().all())

    @staticmethod
    async def get_all_businesses(db: AsyncSession) -> List[Business]:
        """Retrieve all business profiles in the system (for officers and admins)."""
        result = await db.execute(select(Business))
        return list(result.scalars().all())

    @classmethod
    async def create_business(
        cls, db: AsyncSession, owner_id: uuid.UUID, schema: BusinessCreate
    ) -> Business:
        """Create a new business profile for an entrepreneur."""
        new_business = Business(
            owner_id=owner_id,
            name=schema.name,
            sector=schema.sector,
            sub_sector=schema.sub_sector,
            state=schema.state,
            district=schema.district,
            city=schema.city,
            investment_amount=schema.investment_amount,
            employee_count=schema.employee_count,
            expected_turnover=schema.expected_turnover,
            operational_stage=schema.operational_stage,
            flexible_attributes=schema.flexible_attributes
        )
        db.add(new_business)
        await db.commit()
        await db.refresh(new_business)
        logger.info(f"Registered new business profile: '{new_business.name}' for owner ID: {owner_id}")
        return new_business

    @classmethod
    async def update_business(
        cls, 
        db: AsyncSession, 
        business_id: uuid.UUID, 
        user_id: uuid.UUID, 
        role: UserRole, 
        schema: BusinessUpdate
    ) -> Business:
        """Update an existing business profile, checking ownership unless user is Admin."""
        business = await cls.get_business_by_id(db, business_id)
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business profile not found"
            )

        # Access check: Only the owner or an ADMIN can update a business profile
        if business.owner_id != user_id and role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this business profile"
            )

        # Update fields dynamically if provided
        update_data = schema.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(business, key, value)

        db.add(business)
        await db.commit()
        await db.refresh(business)
        logger.info(f"Updated business profile ID: {business_id} by user: {user_id}")
        return business

    @classmethod
    async def delete_business(
        cls, 
        db: AsyncSession, 
        business_id: uuid.UUID, 
        user_id: uuid.UUID, 
        role: UserRole
    ) -> bool:
        """Delete a business profile, checking ownership unless user is Admin."""
        business = await cls.get_business_by_id(db, business_id)
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business profile not found"
            )

        # Access check: Only the owner or an ADMIN can delete a business profile
        if business.owner_id != user_id and role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this business profile"
            )

        await db.delete(business)
        await db.commit()
        logger.info(f"Deleted business profile ID: {business_id} by user: {user_id}")
        return True
