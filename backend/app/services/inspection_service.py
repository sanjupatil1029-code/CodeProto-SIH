import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.workflows import BusinessApproval, ApprovalStatus
from app.models.inspection import Inspection, InspectionStatus
from app.schemas.inspection import (
    InspectionScheduleSchema,
    InspectionRescheduleSchema,
    InspectionReportSchema,
)
from app.services.workflow_service import WorkflowService
from app.core.logging import logger


class InspectionService:
    """
    Module 12: Inspection Management Service.
    Handles inspection scheduling, officer assignment, rescheduling, checklist findings,
    and workflow state transitions.
    """

    @classmethod
    async def schedule_inspection(
        cls,
        db: AsyncSession,
        schema: InspectionScheduleSchema
    ) -> Inspection:
        """Schedule a new inspection for a business approval."""
        res = await db.execute(select(BusinessApproval).where(BusinessApproval.id == schema.approval_id))
        approval = res.scalars().first()
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business approval record not found"
            )

        inspection = Inspection(
            business_id=approval.business_id,
            approval_id=approval.id,
            officer_id=schema.officer_id,
            title=schema.title,
            status=InspectionStatus.SCHEDULED,
            scheduled_date=schema.scheduled_date,
            location_address=schema.location_address
        )
        db.add(inspection)

        # Update approval status to INSPECTION_PENDING
        approval.status = ApprovalStatus.INSPECTION_PENDING
        history = list(approval.stage_history or [])
        history.append({
            "status": ApprovalStatus.INSPECTION_PENDING.value,
            "timestamp": datetime.utcnow().isoformat(),
            "notes": f"Inspection scheduled: '{schema.title}' on {schema.scheduled_date.strftime('%Y-%m-%d %H:%M')}"
        })
        approval.stage_history = history
        db.add(approval)

        await db.commit()
        await db.refresh(inspection)
        logger.info(f"Inspection '{schema.title}' scheduled for approval ID: {approval.id}")
        return inspection

    @classmethod
    async def reschedule_inspection(
        cls,
        db: AsyncSession,
        inspection_id: uuid.UUID,
        schema: InspectionRescheduleSchema
    ) -> Inspection:
        """Reschedule an existing inspection date."""
        res = await db.execute(select(Inspection).where(Inspection.id == inspection_id))
        inspection = res.scalars().first()
        if not inspection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inspection record not found"
            )

        inspection.scheduled_date = schema.new_scheduled_date
        inspection.status = InspectionStatus.RESCHEDULED
        inspection.inspector_notes = f"Rescheduled: {schema.reason}"

        db.add(inspection)
        await db.commit()
        await db.refresh(inspection)
        logger.info(f"Rescheduled inspection {inspection_id} to {schema.new_scheduled_date}")
        return inspection

    @classmethod
    async def submit_inspection_report(
        cls,
        db: AsyncSession,
        inspection_id: uuid.UUID,
        schema: InspectionReportSchema
    ) -> Inspection:
        """Submit statutory findings and complete or fail an inspection."""
        res = await db.execute(select(Inspection).where(Inspection.id == inspection_id))
        inspection = res.scalars().first()
        if not inspection:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inspection record not found"
            )

        inspection.status = schema.status
        inspection.actual_inspection_date = datetime.utcnow()
        inspection.inspector_notes = schema.inspector_notes
        inspection.findings_summary = schema.findings_summary
        inspection.checklist_results = schema.checklist_results or []

        # Update approval status based on inspection outcome
        app_res = await db.execute(select(BusinessApproval).where(BusinessApproval.id == inspection.approval_id))
        approval = app_res.scalars().first()
        if approval:
            if schema.status == InspectionStatus.COMPLETED:
                approval.status = ApprovalStatus.APPROVED
                approval.completed_at = datetime.utcnow()
                # Trigger dependency unlocks
                await WorkflowService._unlock_dependencies(db, approval.business_id)
            elif schema.status == InspectionStatus.FAILED:
                approval.status = ApprovalStatus.REJECTED

            history = list(approval.stage_history or [])
            history.append({
                "status": approval.status.value,
                "timestamp": datetime.utcnow().isoformat(),
                "notes": f"Inspection report submitted: Status {schema.status.value}. Findings: {schema.findings_summary or 'Completed cleanly'}"
            })
            approval.stage_history = history
            db.add(approval)

        db.add(inspection)
        await db.commit()
        await db.refresh(inspection)
        logger.info(f"Inspection report submitted for {inspection_id}: Status {schema.status.value}")
        return inspection

    @classmethod
    async def get_business_inspections(
        cls,
        db: AsyncSession,
        business_id: uuid.UUID
    ) -> List[Inspection]:
        """Fetch all inspections for a business profile."""
        res = await db.execute(
            select(Inspection)
            .where(Inspection.business_id == business_id)
            .order_by(Inspection.created_at.desc())
        )
        return list(res.scalars().all())
