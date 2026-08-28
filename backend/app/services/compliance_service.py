import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.workflows import BusinessApproval, ApprovalStatus
from app.schemas.compliance import (
    CertificateDatesUpdate,
    RenewalItemOut,
    ComplianceDashboardOut,
)
from app.core.logging import logger


class ComplianceService:
    """
    Module 10: Compliance & Renewal Engine Service.
    Handles certificate issue/expiry date updates, configurable reminder thresholds
    (90d, 60d, 30d, 15d, 7d, 1d), and dashboard status reporting.
    """

    REMINDER_THRESHOLDS = [90, 60, 30, 15, 7, 1]

    @classmethod
    async def update_certificate_dates(
        cls,
        db: AsyncSession,
        approval_id: uuid.UUID,
        schema: CertificateDatesUpdate
    ) -> BusinessApproval:
        """Assign or update certificate issue and expiration dates."""
        result = await db.execute(select(BusinessApproval).where(BusinessApproval.id == approval_id))
        approval = result.scalars().first()
        if not approval:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business approval record not found"
            )

        approval.issue_date = schema.issue_date

        if schema.expiry_date:
            approval.expiry_date = schema.expiry_date
        elif schema.validity_years:
            days = int(schema.validity_years * 365)
            approval.expiry_date = schema.issue_date + timedelta(days=days)
        else:
            # Default 1-year validity if unspecified
            approval.expiry_date = schema.issue_date + timedelta(days=365)

        reminder_days = schema.renewal_reminder_days or 30
        approval.renewal_reminder_days = reminder_days
        approval.renewal_deadline = approval.expiry_date
        approval.renewal_start_date = approval.expiry_date - timedelta(days=reminder_days)

        # Recalculate status immediately
        now = datetime.utcnow()
        if now >= approval.expiry_date:
            approval.renewal_status = "EXPIRED"
            approval.status = ApprovalStatus.EXPIRED
        else:
            days_left = (approval.expiry_date - now).days
            if days_left <= 7:
                approval.renewal_status = "CRITICAL_RENEWAL"
            elif days_left <= reminder_days:
                approval.renewal_status = "RENEWAL_DUE"
            else:
                approval.renewal_status = "UP_TO_DATE"

        history = list(approval.stage_history or [])
        history.append({
            "status": approval.renewal_status,
            "timestamp": now.isoformat(),
            "notes": f"Certificate dates updated: Issued {approval.issue_date.strftime('%Y-%m-%d')}, Expires {approval.expiry_date.strftime('%Y-%m-%d')}"
        })
        approval.stage_history = history

        db.add(approval)
        await db.commit()
        await db.refresh(approval)
        logger.info(f"Updated certificate dates for approval '{approval.name}': Expiry {approval.expiry_date}")
        return approval

    @classmethod
    async def evaluate_business_renewals(
        cls,
        db: AsyncSession,
        business_id: uuid.UUID
    ) -> ComplianceDashboardOut:
        """
        Periodically or dynamically check all approval expiration dates for a business profile.
        Evaluates 90d, 60d, 30d, 15d, 7d, 1d thresholds and updates DB state.
        """
        result = await db.execute(
            select(BusinessApproval)
            .where(BusinessApproval.business_id == business_id)
            .order_by(BusinessApproval.created_at.asc())
        )
        approvals = list(result.scalars().all())

        now = datetime.utcnow()
        items: List[RenewalItemOut] = []

        up_to_date_count = 0
        renewal_due_count = 0
        critical_renewal_count = 0
        expired_count = 0

        for app in approvals:
            if not app.expiry_date:
                # If no explicit expiry date set, default to 1 year after created_at / completed_at
                base_date = app.completed_at or app.created_at
                app.expiry_date = base_date + timedelta(days=365)
                app.renewal_deadline = app.expiry_date
                app.renewal_start_date = app.expiry_date - timedelta(days=app.renewal_reminder_days or 30)

            days_left = (app.expiry_date - now).days
            triggered_threshold: Optional[int] = None

            # Determine reminder threshold triggered
            for t in cls.REMINDER_THRESHOLDS:
                if days_left <= t:
                    triggered_threshold = t

            if days_left <= 0:
                app.renewal_status = "EXPIRED"
                if app.status == ApprovalStatus.APPROVED:
                    app.status = ApprovalStatus.EXPIRED
                expired_count += 1
            elif days_left <= 7:
                app.renewal_status = "CRITICAL_RENEWAL"
                if app.status == ApprovalStatus.APPROVED:
                    app.status = ApprovalStatus.RENEWAL_DUE
                critical_renewal_count += 1
            elif days_left <= (app.renewal_reminder_days or 30):
                app.renewal_status = "RENEWAL_DUE"
                if app.status == ApprovalStatus.APPROVED:
                    app.status = ApprovalStatus.RENEWAL_DUE
                renewal_due_count += 1
            else:
                app.renewal_status = "UP_TO_DATE"
                up_to_date_count += 1

            db.add(app)

            items.append(
                RenewalItemOut(
                    approval_id=app.id,
                    rule_code=app.rule_code,
                    approval_name=app.name,
                    responsible_authority=app.responsible_authority,
                    issue_date=app.issue_date,
                    expiry_date=app.expiry_date,
                    days_until_expiry=days_left,
                    renewal_status=app.renewal_status,
                    renewal_deadline=app.renewal_deadline,
                    reminder_threshold_triggered=triggered_threshold
                )
            )

        await db.commit()
        logger.info(f"Evaluated renewals for business {business_id}: {expired_count} expired, {critical_renewal_count} critical, {renewal_due_count} due.")

        return ComplianceDashboardOut(
            business_id=business_id,
            total_licenses=len(approvals),
            up_to_date_count=up_to_date_count,
            renewal_due_count=renewal_due_count,
            critical_renewal_count=critical_renewal_count,
            expired_count=expired_count,
            renewals=items
        )
