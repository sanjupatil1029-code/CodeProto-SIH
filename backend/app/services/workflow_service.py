import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.auth import UserRole
from app.models.business import Business
from app.models.rules import ApprovalRule, RuleStatus
from app.models.workflows import BusinessApproval, ApprovalStatus
from app.services.rule_engine_service import RuleEngineService
from app.core.logging import logger


class WorkflowService:

    @classmethod
    async def get_approval_by_id(cls, db: AsyncSession, approval_id: uuid.UUID) -> Optional[BusinessApproval]:
        """Fetch a business approval record by its ID."""
        result = await db.execute(select(BusinessApproval).where(BusinessApproval.id == approval_id))
        return result.scalars().first()

    @classmethod
    async def get_roadmap(cls, db: AsyncSession, business_id: uuid.UUID) -> List[BusinessApproval]:
        """Retrieve the roadmap (all approvals) for a specific business."""
        result = await db.execute(
            select(BusinessApproval)
            .where(BusinessApproval.business_id == business_id)
            .order_by(BusinessApproval.created_at.asc())
        )
        return list(result.scalars().all())

    @classmethod
    async def generate_roadmap(cls, db: AsyncSession, business_id: uuid.UUID) -> List[BusinessApproval]:
        """Runs the rule engine, generates the applicable approvals, and resolves initial statuses."""
        # 1. Fetch the business to ensure it exists
        business_res = await db.execute(select(Business).where(Business.id == business_id))
        business = business_res.scalars().first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business profile not found"
            )

        # 2. Get evaluated rules from Rule Engine
        evaluation_results = await RuleEngineService.evaluate_business_approvals(db, business_id)
        applicable_codes = {r.rule_code: r for r in evaluation_results if r.status == "APPLICABLE"}

        # 3. Fetch existing business approvals
        existing_approvals = await cls.get_roadmap(db, business_id)
        existing_map = {a.rule_code: a for a in existing_approvals}

        # 4. Remove any business approvals that are no longer applicable
        # (Only if they haven't progressed past NOT_STARTED / READY / BLOCKED to avoid data loss)
        for code, approval in existing_map.items():
            if code not in applicable_codes and approval.status in [
                ApprovalStatus.NOT_STARTED,
                ApprovalStatus.READY,
                ApprovalStatus.BLOCKED
            ]:
                await db.delete(approval)
                logger.info(f"Removed non-applicable approval '{approval.name}' ({code}) from business roadmap.")

        # 5. Add or update applicable approvals
        for code, eval_rule in applicable_codes.items():
            if code not in existing_map:
                new_approval = BusinessApproval(
                    business_id=business_id,
                    rule_code=code,
                    name=eval_rule.name,
                    category=eval_rule.category.value,
                    responsible_authority=eval_rule.responsible_authority,
                    status=ApprovalStatus.NOT_STARTED,  # Set temporarily; resolved below
                    sla_days=eval_rule.sla_days
                )
                db.add(new_approval)
                logger.info(f"Added applicable approval '{eval_rule.name}' ({code}) to business roadmap.")
            else:
                # Update metadata if changed
                approval = existing_map[code]
                approval.name = eval_rule.name
                approval.responsible_authority = eval_rule.responsible_authority
                approval.sla_days = eval_rule.sla_days
                db.add(approval)

        await db.commit()

        # 6. Re-evaluate dependencies and update statuses
        # Fetch fresh roadmap from DB (including newly added records)
        roadmap = await cls.get_roadmap(db, business_id)
        roadmap_map = {a.rule_code: a for a in roadmap}

        # Get rules to check dependencies definitions
        rules_res = await db.execute(
            select(ApprovalRule).where(ApprovalRule.status == RuleStatus.ACTIVE)
        )
        rules_map = {r.code: r for r in rules_res.scalars().all()}

        for approval in roadmap:
            # We only touch NOT_STARTED, BLOCKED, or READY statuses during dynamic resolution
            if approval.status not in [ApprovalStatus.NOT_STARTED, ApprovalStatus.BLOCKED, ApprovalStatus.READY]:
                continue

            rule = rules_map.get(approval.rule_code)
            if not rule or not rule.dependencies:
                # No dependencies -> READY
                approval.status = ApprovalStatus.READY
            else:
                # Check if any dependencies are blocking
                is_blocked = False
                for dep_code in rule.dependencies:
                    dep_approval = roadmap_map.get(dep_code)
                    # Blocked if the dependency is applicable (on roadmap) and not yet APPROVED
                    if dep_approval and dep_approval.status != ApprovalStatus.APPROVED:
                        is_blocked = True
                        break
                
                approval.status = ApprovalStatus.BLOCKED if is_blocked else ApprovalStatus.READY
            
            db.add(approval)

        await db.commit()
        logger.info(f"Resolved and updated approval roadmap dependencies for business ID: {business_id}")
        
        # Return updated roadmap
        return await cls.get_roadmap(db, business_id)

    @classmethod
    async def update_approval_status(
        cls, 
        db: AsyncSession, 
        approval_id: uuid.UUID, 
        user_id: uuid.UUID, 
        role: UserRole, 
        target_status: ApprovalStatus
    ) -> BusinessApproval:
        """Update status of a business approval, calculating SLAs and triggering dependency unlocks."""
        # 1. Fetch approval
        approval = await cls.get_approval_by_id(db, approval_id)
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business approval record not found"
            )

        # 2. Check permissions via Business ownership
        business_res = await db.execute(select(Business).where(Business.id == approval.business_id))
        business = business_res.scalars().first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated business profile not found"
            )

        # Permission check: Entrepreneur role restrictions
        if role == UserRole.ENTREPRENEUR:
            if business.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not own the business associated with this approval"
                )
            # Entrepreneurs can only start applications (Ready/Not Started -> In Progress)
            if approval.status not in [ApprovalStatus.READY, ApprovalStatus.NOT_STARTED]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only officers/admins can update status once the application has started"
                )
            if target_status != ApprovalStatus.IN_PROGRESS:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Entrepreneurs can only set status to IN_PROGRESS"
                )

        # 3. Apply state change values (SLA dates, completed dates)
        old_status = approval.status
        approval.status = target_status

        if target_status == ApprovalStatus.IN_PROGRESS and old_status != ApprovalStatus.IN_PROGRESS:
            approval.started_at = datetime.utcnow()
            approval.sla_deadline = datetime.utcnow() + timedelta(days=approval.sla_days)
        elif target_status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
            approval.completed_at = datetime.utcnow()

        db.add(approval)
        await db.commit()
        await db.refresh(approval)
        logger.info(f"Updated approval status '{approval.name}' ({approval.rule_code}) to {target_status} by user: {user_id}")

        # 4. If status is APPROVED, unlock dependent rules recursively
        if target_status == ApprovalStatus.APPROVED:
            await cls._unlock_dependencies(db, approval.business_id)

        await db.commit()
        return approval

    @classmethod
    async def _unlock_dependencies(cls, db: AsyncSession, business_id: uuid.UUID):
        """Internal helper to scan and unlock blocked business approvals whose dependencies are now met."""
        roadmap = await cls.get_roadmap(db, business_id)
        roadmap_map = {a.rule_code: a for a in roadmap}

        # Fetch rules map for dependency declarations
        rules_res = await db.execute(
            select(ApprovalRule).where(ApprovalRule.status == RuleStatus.ACTIVE)
        )
        rules_map = {r.code: r for r in rules_res.scalars().all()}

        unlocked_any = False
        for approval in roadmap:
            if approval.status != ApprovalStatus.BLOCKED:
                continue

            rule = rules_map.get(approval.rule_code)
            if not rule:
                continue

            # Verify if all dependencies are now APPROVED
            is_blocked = False
            for dep_code in rule.dependencies:
                dep_approval = roadmap_map.get(dep_code)
                if dep_approval and dep_approval.status != ApprovalStatus.APPROVED:
                    is_blocked = True
                    break

            if not is_blocked:
                approval.status = ApprovalStatus.READY
                db.add(approval)
                unlocked_any = True
                logger.info(f"Dependency met: Unlocked approval '{approval.name}' ({approval.rule_code}) to READY.")

        if unlocked_any:
            # Commit the batch and recursively check again (in case unlocking one unlocks another down the chain)
            await db.commit()
            await cls._unlock_dependencies(db, business_id)
