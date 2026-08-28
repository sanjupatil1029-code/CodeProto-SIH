import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.rules import ApprovalRule, RuleStatus
from app.models.regulatory_update import RegulatoryUpdate, UpdateStatus
from app.models.workflows import BusinessApproval
from app.schemas.regulatory_update import (
    RegulatoryUpdateCreateSchema,
    RegulatoryUpdateOut,
    RuleVersionItemOut,
    RuleVersionHistoryOut,
)
from app.core.logging import logger


class RegulatoryUpdateService:
    """
    Module 15: Regulatory Update & Rule Versioning Service.
    Handles government gazette notification intake, AI-assisted rule diff extraction,
    admin review approval pipeline, immutable rule versioning (Version 1.0 -> Version 2.0),
    and automatic re-evaluation of affected business roadmaps.
    """

    @classmethod
    async def propose_regulatory_update(
        cls,
        db: AsyncSession,
        schema: RegulatoryUpdateCreateSchema
    ) -> RegulatoryUpdate:
        """Create a new proposed regulatory update draft awaiting admin review."""
        reg_update = RegulatoryUpdate(
            title=schema.title,
            source_authority=schema.source_authority,
            rule_code=schema.rule_code,
            summary=schema.summary,
            extracted_changes=schema.extracted_changes,
            impact_summary=schema.impact_summary,
            status=UpdateStatus.DRAFT_PENDING_REVIEW
        )

        db.add(reg_update)
        await db.commit()
        await db.refresh(reg_update)
        logger.info(f"Proposed regulatory update '{schema.title}' for rule '{schema.rule_code}' (ID: {reg_update.id})")
        return reg_update

    @classmethod
    async def get_pending_updates(cls, db: AsyncSession) -> List[RegulatoryUpdate]:
        """Fetch all draft regulatory updates pending admin review."""
        res = await db.execute(
            select(RegulatoryUpdate)
            .where(RegulatoryUpdate.status == UpdateStatus.DRAFT_PENDING_REVIEW)
            .order_by(RegulatoryUpdate.created_at.desc())
        )
        return list(res.scalars().all())

    @classmethod
    async def review_regulatory_update(
        cls,
        db: AsyncSession,
        update_id: uuid.UUID,
        approve: bool,
        admin_user_id: uuid.UUID,
        review_notes: Optional[str] = None
    ) -> RegulatoryUpdate:
        """
        Admin Review Pipeline:
        If approved:
        1. Supersedes existing active rule version (sets is_latest = False, effective_to = now).
        2. Creates NEW ApprovalRule version (Version 2.0) with updated attributes (NEVER overwrites old version!).
        3. Updates status to APPROVED and re-evaluates active business roadmaps.
        If rejected:
        1. Marks update status as REJECTED.
        """
        res = await db.execute(select(RegulatoryUpdate).where(RegulatoryUpdate.id == update_id))
        reg_update = res.scalars().first()
        if not reg_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Regulatory update record not found"
            )

        reg_update.reviewed_by = admin_user_id
        reg_update.reviewed_at = datetime.utcnow()

        if not approve:
            reg_update.status = UpdateStatus.REJECTED
            db.add(reg_update)
            await db.commit()
            logger.info(f"Regulatory update {update_id} REJECTED by admin {admin_user_id}.")
            return reg_update

        # Approve update and create NEW rule version
        rule_res = await db.execute(
            select(ApprovalRule)
            .where(ApprovalRule.code == reg_update.rule_code)
            .where(ApprovalRule.is_latest == True)
        )
        current_rule = rule_res.scalars().first()
        if not current_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target approval rule '{reg_update.rule_code}' not found in active database."
            )

        now = datetime.utcnow()

        # 1. Supersede current version
        current_rule.is_latest = False
        current_rule.effective_to = now
        current_rule.status = RuleStatus.SUPERSEDED
        db.add(current_rule)

        # 2. Calculate next version string (e.g. "1.0" -> "2.0")
        try:
            old_ver_num = float(current_rule.rule_version)
            next_ver = f"{old_ver_num + 1.0:.1f}"
        except ValueError:
            next_ver = "2.0"

        # 3. Apply extracted rule changes to new version
        changes = reg_update.extracted_changes or {}
        new_sla = int(changes.get("sla_days", current_rule.sla_days))
        
        req_docs = list(current_rule.required_document_types or [])
        if "added_documents" in changes and isinstance(changes["added_documents"], list):
            for doc in changes["added_documents"]:
                if doc not in req_docs:
                    req_docs.append(doc)

        new_rule = ApprovalRule(
            code=current_rule.code,
            name=f"{current_rule.name} (v{next_ver})",
            category=current_rule.category,
            jurisdiction=current_rule.jurisdiction,
            state=current_rule.state,
            responsible_authority=current_rule.responsible_authority,
            sla_days=new_sla,
            inspection_required=current_rule.inspection_required,
            renewal_required=current_rule.renewal_required,
            renewal_interval_months=current_rule.renewal_interval_months,
            conditions=current_rule.conditions,
            required_document_types=req_docs,
            dependencies=current_rule.dependencies,
            explanation=f"Updated via Gazette Notification: {reg_update.title}. Impact: {reg_update.impact_summary}",
            rule_version=next_ver,
            is_latest=True,
            status=RuleStatus.ACTIVE,
            effective_from=now
        )
        db.add(new_rule)

        # 4. Mark update APPROVED
        reg_update.status = UpdateStatus.APPROVED
        db.add(reg_update)

        # 5. Re-evaluate affected business approval SLA & requirement records
        biz_approvals_res = await db.execute(
            select(BusinessApproval).where(BusinessApproval.rule_code == reg_update.rule_code)
        )
        affected_approvals = list(biz_approvals_res.scalars().all())
        for app in affected_approvals:
            app.sla_days = new_sla
            history = list(app.stage_history or [])
            history.append({
                "status": app.status.value,
                "timestamp": now.isoformat(),
                "notes": f"Regulatory Rule Version Upgraded to v{next_ver} via Official Gazette Notification: {reg_update.title}."
            })
            app.stage_history = history
            db.add(app)

        await db.commit()
        await db.refresh(reg_update)
        logger.info(f"Approved Regulatory Update {update_id}. Created Rule Version v{next_ver} for rule '{reg_update.rule_code}'. Updated {len(affected_approvals)} business roadmaps.")
        return reg_update

    @classmethod
    async def get_rule_version_history(
        cls,
        db: AsyncSession,
        rule_code: str
    ) -> RuleVersionHistoryOut:
        """Fetch full immutable version audit history for an approval rule."""
        res = await db.execute(
            select(ApprovalRule)
            .where(ApprovalRule.code == rule_code)
            .order_by(ApprovalRule.created_at.desc())
        )
        rules = list(res.scalars().all())
        if not rules:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No rule records found for code '{rule_code}'"
            )

        items = [
            RuleVersionItemOut(
                rule_id=r.id,
                rule_code=r.code,
                rule_version=r.rule_version,
                name=r.name,
                sla_days=r.sla_days,
                is_latest=r.is_latest,
                status=r.status.value,
                effective_from=r.effective_from,
                effective_to=r.effective_to,
                created_at=r.created_at
            )
            for r in rules
        ]

        return RuleVersionHistoryOut(
            rule_code=rule_code,
            name=rules[0].name,
            versions_count=len(rules),
            versions=items
        )
