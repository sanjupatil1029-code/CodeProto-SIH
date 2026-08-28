import uuid
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.grievance import (
    Grievance,
    GrievanceStatus,
    GrievancePriority,
    GrievanceCategory,
)
from app.schemas.grievance import GrievanceCreateSchema
from app.core.logging import logger


class GrievanceService:
    """
    Module 13: Grievance and Multi-Tier Escalation Engine Service.
    Handles grievance ticketing, officer assignment, resolution SLA tracking,
    and automatic multi-tier escalation (Level 1 Nodal -> Level 2 Senior -> Level 3 Secretariat).
    """

    # Resolution SLA days based on priority
    PRIORITY_SLA_HOURS = {
        GrievancePriority.CRITICAL: 24,   # 1 Day
        GrievancePriority.HIGH: 48,       # 2 Days
        GrievancePriority.MEDIUM: 168,    # 7 Days
        GrievancePriority.LOW: 336,       # 14 Days
    }

    LEVEL_TITLES = {
        1: "Level 1 Nodal Officer",
        2: "Level 2 Regional Director / Senior Inspector",
        3: "Level 3 Department Secretariat / State Nodal Authority",
    }

    @classmethod
    async def create_grievance(
        cls,
        db: AsyncSession,
        complainant_id: uuid.UUID,
        schema: GrievanceCreateSchema
    ) -> Grievance:
        """Create a new grievance ticket and calculate resolution SLA deadline."""
        now = datetime.utcnow()
        hours = cls.PRIORITY_SLA_HOURS.get(schema.priority, 168)
        deadline = now + timedelta(hours=hours)

        grievance = Grievance(
            business_id=schema.business_id,
            approval_id=schema.approval_id,
            complainant_id=complainant_id,
            title=schema.title,
            description=schema.description,
            category=schema.category,
            priority=schema.priority,
            department=schema.department or "General Authority",
            status=GrievanceStatus.OPEN,
            escalation_level=1,
            resolution_deadline=deadline,
            escalation_history=[{
                "level": 1,
                "title": cls.LEVEL_TITLES[1],
                "escalated_at": now.isoformat(),
                "reason": "Grievance ticket created."
            }]
        )

        db.add(grievance)
        await db.commit()
        await db.refresh(grievance)
        logger.info(f"Grievance created '{schema.title}' (ID: {grievance.id}) - Priority: {schema.priority.value}")
        return grievance

    @classmethod
    async def assign_officer(
        cls,
        db: AsyncSession,
        grievance_id: uuid.UUID,
        officer_id: uuid.UUID
    ) -> Grievance:
        """Assign an officer to handle the grievance."""
        res = await db.execute(select(Grievance).where(Grievance.id == grievance_id))
        grievance = res.scalars().first()
        if not grievance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance record not found"
            )

        grievance.assigned_officer_id = officer_id
        if grievance.status in [GrievanceStatus.OPEN, GrievanceStatus.ESCALATED]:
            grievance.status = GrievanceStatus.ASSIGNED

        history = list(grievance.escalation_history or [])
        history.append({
            "level": grievance.escalation_level,
            "timestamp": datetime.utcnow().isoformat(),
            "action": f"Officer assigned: {officer_id}"
        })
        grievance.escalation_history = history

        db.add(grievance)
        await db.commit()
        await db.refresh(grievance)
        logger.info(f"Assigned officer {officer_id} to grievance {grievance_id}")
        return grievance

    @classmethod
    async def resolve_grievance(
        cls,
        db: AsyncSession,
        grievance_id: uuid.UUID,
        resolution_notes: str,
        officer_id: Optional[uuid.UUID] = None
    ) -> Grievance:
        """Mark grievance as resolved and log resolution notes."""
        res = await db.execute(select(Grievance).where(Grievance.id == grievance_id))
        grievance = res.scalars().first()
        if not grievance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance record not found"
            )

        grievance.status = GrievanceStatus.RESOLVED
        grievance.resolution_notes = resolution_notes

        history = list(grievance.escalation_history or [])
        history.append({
            "level": grievance.escalation_level,
            "timestamp": datetime.utcnow().isoformat(),
            "action": f"Grievance resolved cleanly. Notes: {resolution_notes}"
        })
        grievance.escalation_history = history

        db.add(grievance)
        await db.commit()
        await db.refresh(grievance)
        logger.info(f"Grievance {grievance_id} resolved cleanly.")
        return grievance

    @classmethod
    async def check_and_escalate_grievances(
        cls,
        db: AsyncSession,
        business_id: uuid.UUID
    ) -> List[Grievance]:
        """
        Scan all active grievances for a business profile past their resolution deadline.
        Automatically escalates level (1 -> 2 -> 3) and records escalation audit logs.
        """
        res = await db.execute(
            select(Grievance)
            .where(Grievance.business_id == business_id)
            .where(Grievance.status.in_([GrievanceStatus.OPEN, GrievanceStatus.ASSIGNED, GrievanceStatus.IN_PROGRESS, GrievanceStatus.ESCALATED]))
        )
        grievances = list(res.scalars().all())

        now = datetime.utcnow()
        escalated_list: List[Grievance] = []

        for g in grievances:
            if g.resolution_deadline and now > g.resolution_deadline and g.escalation_level < 3:
                g.escalation_level += 1
                g.status = GrievanceStatus.ESCALATED

                # Extend deadline for higher tier level
                hours = cls.PRIORITY_SLA_HOURS.get(g.priority, 168)
                g.resolution_deadline = now + timedelta(hours=hours)

                history = list(g.escalation_history or [])
                history.append({
                    "level": g.escalation_level,
                    "title": cls.LEVEL_TITLES.get(g.escalation_level, f"Level {g.escalation_level}"),
                    "escalated_at": now.isoformat(),
                    "reason": f"Automatic Escalation: SLA Resolution Deadline exceeded for Level {g.escalation_level - 1}."
                })
                g.escalation_history = history

                db.add(g)
                escalated_list.append(g)
                logger.info(f"Grievance {g.id} escalated to Level {g.escalation_level} ({cls.LEVEL_TITLES.get(g.escalation_level)})")

        if escalated_list:
            await db.commit()

        return await cls.get_business_grievances(db, business_id)

    @classmethod
    async def get_business_grievances(
        cls,
        db: AsyncSession,
        business_id: uuid.UUID
    ) -> List[Grievance]:
        """Retrieve all grievances for a business profile."""
        res = await db.execute(
            select(Grievance)
            .where(Grievance.business_id == business_id)
            .order_by(Grievance.created_at.desc())
        )
        return list(res.scalars().all())
