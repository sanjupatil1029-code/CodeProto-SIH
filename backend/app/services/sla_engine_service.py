import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.workflows import BusinessApproval, ApprovalStatus
from app.schemas.compliance import (
    SLABreachItemOut,
    DepartmentBottleneckOut,
    SLABottleneckAnalyticsOut,
)
from app.core.logging import logger


class SLAEngineService:
    """
    Module 11: SLA and Bottleneck Engine Service.
    Calculates SLA elapsed percentages, flags SLA_WARNING (>=80%) and SLA_BREACHED (>=100%),
    and aggregates department/authority bottleneck analytics.
    """

    ACTIVE_STATUSES = [
        ApprovalStatus.IN_PROGRESS,
        ApprovalStatus.SUBMITTED,
        ApprovalStatus.UNDER_REVIEW,
        ApprovalStatus.INSPECTION_PENDING,
        ApprovalStatus.QUERY_RAISED,
        ApprovalStatus.OFFICIAL_PORTAL_HANDOFF,
        ApprovalStatus.READY_FOR_SUBMISSION,
    ]

    @classmethod
    async def evaluate_business_slas(
        cls,
        db: AsyncSession,
        business_id: uuid.UUID
    ) -> SLABottleneckAnalyticsOut:
        """Scan active approvals for a business profile and compute SLA compliance metrics."""
        result = await db.execute(
            select(BusinessApproval)
            .where(BusinessApproval.business_id == business_id)
            .order_by(BusinessApproval.created_at.asc())
        )
        approvals = list(result.scalars().all())

        now = datetime.utcnow()
        active_items: List[SLABreachItemOut] = []

        on_track_count = 0
        warning_count = 0
        breached_count = 0

        # Authority grouping for bottleneck analysis
        authority_map: Dict[str, Dict[str, Any]] = {}

        for app in approvals:
            # Initialize authority tracking dict
            auth_name = app.responsible_authority or "Local Authority"
            if auth_name not in authority_map:
                authority_map[auth_name] = {
                    "total": 0,
                    "in_progress": 0,
                    "breached": 0,
                    "processing_days_sum": 0.0,
                    "completed_count": 0
                }

            authority_map[auth_name]["total"] += 1

            if app.status in cls.ACTIVE_STATUSES or app.status == ApprovalStatus.APPROVED:
                start_time = app.submitted_at or app.started_at or app.created_at
                if not app.sla_deadline:
                    app.sla_deadline = start_time + timedelta(days=app.sla_days)

                if app.status == ApprovalStatus.APPROVED and app.completed_at:
                    elapsed_sec = (app.completed_at - start_time).total_seconds()
                    authority_map[auth_name]["processing_days_sum"] += max(0.1, elapsed_sec / 86400.0)
                    authority_map[auth_name]["completed_count"] += 1
                else:
                    elapsed_sec = (now - start_time).total_seconds()

                elapsed_days = round(max(0.1, elapsed_sec / 86400.0), 1)
                elapsed_pct = round((elapsed_days / max(1, app.sla_days)) * 100.0, 1)
                app.sla_elapsed_percent = elapsed_pct

                if app.status in cls.ACTIVE_STATUSES:
                    authority_map[auth_name]["in_progress"] += 1

                    if now > app.sla_deadline or elapsed_pct >= 100.0:
                        app.sla_status = "SLA_BREACHED"
                        breached_count += 1
                        authority_map[auth_name]["breached"] += 1
                    elif elapsed_pct >= 80.0:
                        app.sla_status = "SLA_WARNING"
                        warning_count += 1
                    else:
                        app.sla_status = "ON_TRACK"
                        on_track_count += 1

                db.add(app)

                active_items.append(
                    SLABreachItemOut(
                        approval_id=app.id,
                        rule_code=app.rule_code,
                        approval_name=app.name,
                        responsible_authority=app.responsible_authority,
                        status=app.status.value,
                        started_at=start_time,
                        sla_days=app.sla_days,
                        sla_deadline=app.sla_deadline,
                        elapsed_days=elapsed_days,
                        elapsed_percent=elapsed_pct,
                        sla_status=app.sla_status
                    )
                )

        await db.commit()

        total_active = on_track_count + warning_count + breached_count
        overall_health = (
            round((on_track_count / max(1, total_active)) * 100.0, 1)
            if total_active > 0
            else 100.0
        )

        # Build department bottleneck list
        department_bottlenecks: List[DepartmentBottleneckOut] = []
        for auth_name, data in authority_map.items():
            completed_c = data["completed_count"]
            avg_days = round(
                data["processing_days_sum"] / max(1, completed_c), 1
            ) if completed_c > 0 else 5.0

            breached_c = data["breached"]
            if breached_c >= 3:
                risk_level = "CRITICAL"
            elif breached_c == 2:
                risk_level = "HIGH"
            elif breached_c == 1:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            department_bottlenecks.append(
                DepartmentBottleneckOut(
                    authority=auth_name,
                    total_applications=data["total"],
                    in_progress_count=data["in_progress"],
                    sla_breached_count=data["breached"],
                    average_processing_days=avg_days,
                    bottleneck_risk_level=risk_level
                )
            )

        logger.info(f"SLA Analytics evaluated for business {business_id}: Health {overall_health}%, Breached: {breached_count}")

        return SLABottleneckAnalyticsOut(
            business_id=business_id,
            total_active_applications=total_active,
            on_track_count=on_track_count,
            warning_count=warning_count,
            breached_count=breached_count,
            overall_sla_health_percent=overall_health,
            applications=active_items,
            department_bottlenecks=department_bottlenecks
        )
