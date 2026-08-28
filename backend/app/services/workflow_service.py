import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.auth import UserRole
from app.models.business import Business
from app.models.rules import ApprovalRule, RuleStatus
from app.models.workflows import BusinessApproval, ApprovalStatus, IntegrationMode
from app.schemas.workflows import (
    WorkflowHandoffResponse,
    WorkflowSubmitResponse,
    AdapterStatusSyncResponse,
)
from app.adapters.factory import AdapterFactory
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
        business_res = await db.execute(select(Business).where(Business.id == business_id))
        business = business_res.scalars().first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business profile not found"
            )

        evaluation_results = await RuleEngineService.evaluate_business_approvals(db, business_id)
        applicable_codes = {r.rule_code: r for r in evaluation_results if r.status in ["APPLICABLE", "NEEDS_MORE_INFO"]}

        existing_approvals = await cls.get_roadmap(db, business_id)
        existing_map = {a.rule_code: a for a in existing_approvals}

        # Remove non-applicable non-started approvals
        for code, approval in existing_map.items():
            if code not in applicable_codes and approval.status in [
                ApprovalStatus.NOT_STARTED,
                ApprovalStatus.READY,
                ApprovalStatus.BLOCKED
            ]:
                await db.delete(approval)

        # Add or update applicable approvals
        for code, eval_rule in applicable_codes.items():
            adapter = AdapterFactory.get_adapter(code)
            if code not in existing_map:
                new_approval = BusinessApproval(
                    business_id=business_id,
                    rule_code=code,
                    name=eval_rule.name,
                    category=eval_rule.category.value,
                    responsible_authority=eval_rule.responsible_authority,
                    status=ApprovalStatus.NOT_STARTED,
                    external_system=adapter.system_name,
                    integration_mode=adapter.integration_mode.value,
                    official_portal_url=adapter.get_official_portal_url(),
                    sla_days=eval_rule.sla_days,
                    stage_history=[{
                        "status": ApprovalStatus.NOT_STARTED.value,
                        "timestamp": datetime.utcnow().isoformat(),
                        "notes": f"Roadmap entry generated. Assigned adapter: {adapter.system_name}"
                    }]
                )
                db.add(new_approval)
            else:
                approval = existing_map[code]
                approval.name = eval_rule.name
                approval.responsible_authority = eval_rule.responsible_authority
                approval.sla_days = eval_rule.sla_days
                approval.external_system = adapter.system_name
                approval.integration_mode = adapter.integration_mode.value
                approval.official_portal_url = adapter.get_official_portal_url()
                db.add(approval)

        await db.commit()

        # Re-evaluate dependencies
        roadmap = await cls.get_roadmap(db, business_id)
        roadmap_map = {a.rule_code: a for a in roadmap}

        rules_res = await db.execute(
            select(ApprovalRule).where(ApprovalRule.status == RuleStatus.ACTIVE)
        )
        rules_map = {r.code: r for r in rules_res.scalars().all()}

        for approval in roadmap:
            if approval.status not in [ApprovalStatus.NOT_STARTED, ApprovalStatus.BLOCKED, ApprovalStatus.READY]:
                continue

            rule = rules_map.get(approval.rule_code)
            if not rule or not rule.dependencies:
                approval.status = ApprovalStatus.READY
            else:
                is_blocked = False
                for dep_code in rule.dependencies:
                    dep_approval = roadmap_map.get(dep_code)
                    if dep_approval and dep_approval.status != ApprovalStatus.APPROVED:
                        is_blocked = True
                        break
                
                approval.status = ApprovalStatus.BLOCKED if is_blocked else ApprovalStatus.READY
            
            db.add(approval)

        await db.commit()
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
        approval = await cls.get_approval_by_id(db, approval_id)
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business approval record not found"
            )

        business_res = await db.execute(select(Business).where(Business.id == approval.business_id))
        business = business_res.scalars().first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Associated business profile not found"
            )

        if role == UserRole.ENTREPRENEUR:
            if business.owner_id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not own the business associated with this approval"
                )

        old_status = approval.status
        approval.status = target_status

        if target_status in [ApprovalStatus.IN_PROGRESS, ApprovalStatus.SUBMITTED] and not approval.started_at:
            approval.started_at = datetime.utcnow()
            approval.sla_deadline = datetime.utcnow() + timedelta(days=approval.sla_days)
        elif target_status in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
            approval.completed_at = datetime.utcnow()

        history = list(approval.stage_history or [])
        history.append({
            "status": target_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "updated_by": str(user_id)
        })
        approval.stage_history = history

        db.add(approval)
        await db.commit()
        await db.refresh(approval)

        if target_status == ApprovalStatus.APPROVED:
            await cls._unlock_dependencies(db, approval.business_id)

        return approval

    @classmethod
    async def initiate_portal_handoff(
        cls, db: AsyncSession, approval_id: uuid.UUID, user_id: uuid.UUID
    ) -> WorkflowHandoffResponse:
        """
        Module 8 & 9: Initiate official government portal handoff.
        Marks internal workflow status as OFFICIAL_PORTAL_HANDOFF and returns prefilled portal URL.
        """
        approval = await cls.get_approval_by_id(db, approval_id)
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval record not found"
            )

        business_res = await db.execute(select(Business).where(Business.id == approval.business_id))
        business = business_res.scalars().first()

        adapter = AdapterFactory.get_adapter(approval.rule_code)

        biz_context = {
            "name": business.name if business else "Business",
            "sector": business.sector if business else "",
            "expected_turnover": float(business.expected_turnover) if business else 0,
            "state": business.state if business else ""
        }

        handoff_data = await adapter.submit_application(biz_context, [])

        approval.status = ApprovalStatus.OFFICIAL_PORTAL_HANDOFF
        approval.external_system = adapter.system_name
        approval.integration_mode = adapter.integration_mode.value
        approval.official_portal_url = adapter.get_official_portal_url()
        
        if handoff_data.get("external_reference_id"):
            approval.external_reference_id = handoff_data["external_reference_id"]

        history = list(approval.stage_history or [])
        history.append({
            "status": ApprovalStatus.OFFICIAL_PORTAL_HANDOFF.value,
            "timestamp": datetime.utcnow().isoformat(),
            "notes": f"Handoff initiated for {adapter.system_name}. URL: {adapter.get_official_portal_url()}"
        })
        approval.stage_history = history

        db.add(approval)
        await db.commit()

        return WorkflowHandoffResponse(
            approval_id=approval.id,
            workflow_id=approval.workflow_id,
            rule_code=approval.rule_code,
            approval_name=approval.name,
            status=ApprovalStatus.OFFICIAL_PORTAL_HANDOFF,
            external_system=adapter.system_name,
            integration_mode=adapter.integration_mode.value,
            official_portal_url=adapter.get_official_portal_url(),
            handoff_instructions=handoff_data.get("handoff_instructions", f"Please visit {adapter.get_official_portal_url()} to complete submission."),
            prefilled_payload_summary=biz_context
        )

    @classmethod
    async def submit_workflow_application(
        cls, db: AsyncSession, approval_id: uuid.UUID, user_id: uuid.UUID
    ) -> WorkflowSubmitResponse:
        """
        Module 8 & 9: Submit application through Government Integration Adapter Layer.
        Generates external reference ID, sets SLA deadline, and records internal workflow track.
        """
        approval = await cls.get_approval_by_id(db, approval_id)
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval record not found"
            )

        business_res = await db.execute(select(Business).where(Business.id == approval.business_id))
        business = business_res.scalars().first()

        adapter = AdapterFactory.get_adapter(approval.rule_code)

        biz_context = {
            "name": business.name if business else "Business",
            "sector": business.sector if business else "",
            "expected_turnover": float(business.expected_turnover) if business else 0,
            "state": business.state if business else ""
        }

        sub_res = await adapter.submit_application(biz_context, [])

        target_status = ApprovalStatus.SUBMITTED if adapter.integration_mode != IntegrationMode.PORTAL_HANDOFF else ApprovalStatus.OFFICIAL_PORTAL_HANDOFF
        
        approval.status = target_status
        approval.external_system = adapter.system_name
        approval.external_reference_id = sub_res.get("external_reference_id")
        approval.integration_mode = adapter.integration_mode.value
        approval.official_portal_url = adapter.get_official_portal_url()
        approval.submitted_at = datetime.utcnow()
        approval.sla_deadline = datetime.utcnow() + timedelta(days=approval.sla_days)

        history = list(approval.stage_history or [])
        history.append({
            "status": target_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "external_ref": approval.external_reference_id,
            "notes": sub_res.get("handoff_instructions", "Application submitted via adapter layer.")
        })
        approval.stage_history = history

        db.add(approval)
        await db.commit()

        return WorkflowSubmitResponse(
            approval_id=approval.id,
            workflow_id=approval.workflow_id,
            rule_code=approval.rule_code,
            approval_name=approval.name,
            status=target_status,
            external_system=adapter.system_name,
            external_reference_id=approval.external_reference_id or "SUBMITTED",
            integration_mode=adapter.integration_mode.value,
            official_portal_url=adapter.get_official_portal_url(),
            sla_deadline=approval.sla_deadline,
            submission_notes=sub_res.get("handoff_instructions", "Submitted successfully.")
        )

    @classmethod
    async def sync_external_status(
        cls, db: AsyncSession, approval_id: uuid.UUID, user_id: uuid.UUID
    ) -> AdapterStatusSyncResponse:
        """
        Module 8 & 9: Sync status from external government system / mock adapter.
        """
        approval = await cls.get_approval_by_id(db, approval_id)
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Approval record not found"
            )

        adapter = AdapterFactory.get_adapter(approval.rule_code)
        ext_ref = approval.external_reference_id or "MOCK-REF-101"

        status_data = await adapter.get_application_status(ext_ref)

        ext_status_str = status_data.get("status", "IN_PROGRESS")
        try:
            new_status = ApprovalStatus(ext_status_str)
            approval.status = new_status
        except ValueError:
            pass

        history = list(approval.stage_history or [])
        history.append({
            "status": approval.status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "sync_remarks": status_data.get("remarks", "Status synced from external system.")
        })
        approval.stage_history = history

        db.add(approval)
        await db.commit()

        return AdapterStatusSyncResponse(
            approval_id=approval.id,
            external_reference_id=ext_ref,
            external_system=adapter.system_name,
            current_status=approval.status,
            remarks=status_data.get("remarks", "Synced from government adapter."),
            official_portal_url=adapter.get_official_portal_url(),
            synced_at=datetime.utcnow()
        )

    @classmethod
    async def _unlock_dependencies(cls, db: AsyncSession, business_id: uuid.UUID):
        """Internal helper to scan and unlock blocked business approvals whose dependencies are now met."""
        roadmap = await cls.get_roadmap(db, business_id)
        roadmap_map = {a.rule_code: a for a in roadmap}

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

        if unlocked_any:
            await db.commit()
            await cls._unlock_dependencies(db, business_id)
