import asyncio
import os
import sys
import uuid
from datetime import datetime, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core import database
from app.schemas.auth import UserRegister
from app.schemas.business import BusinessCreate
from app.schemas.inspection import (
    InspectionScheduleSchema,
    InspectionRescheduleSchema,
    InspectionReportSchema,
)
from app.schemas.grievance import GrievanceCreateSchema
from app.models.auth import UserRole
from app.models.workflows import ApprovalStatus
from app.models.inspection import InspectionStatus
from app.models.grievance import GrievanceStatus, GrievancePriority, GrievanceCategory
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService
from app.services.workflow_service import WorkflowService
from app.services.inspection_service import InspectionService
from app.services.grievance_service import GrievanceService


async def run_inspections_grievances_tests():
    print("==================================================")
    print(" MODULE 12 & 13: INSPECTION & GRIEVANCE TEST SUITE")
    print("==================================================")

    # 1. Init Database
    db_ok = await database.check_and_fallback_db()
    assert db_ok, "Database connection failed!"
    await database.init_db()
    print("[SUCCESS] 1. Database initialized.")

    async with database.SessionLocal() as db:
        # 2. Register Owner & Officer Users
        owner_email = f"grievance_owner_{uuid.uuid4().hex[:6]}@example.com"
        owner = await AuthService.register_user(
            db, UserRegister(email=owner_email, password="Password123!", full_name="Entrepreneur Owner")
        )

        officer_email = f"inspector_officer_{uuid.uuid4().hex[:6]}@example.com"
        officer = await AuthService.register_user(
            db, UserRegister(email=officer_email, password="Password123!", full_name="Fire Inspector Officer")
        )
        officer.role = UserRole.OFFICER
        db.add(officer)
        await db.commit()

        # 3. Create Business Profile
        biz_schema = BusinessCreate(
            name="Sanjupatil Organic Dairy Processing Ltd",
            sector="FOOD_PROCESSING",
            sub_sector="DAIRY_PROCESSING",
            state="Maharashtra",
            district="Pune",
            city="Pune",
            investment_amount=50000000.0,
            employee_count=75,
            expected_turnover=10000000.0,
            operational_stage="REGISTERED",
            ownership_type="PRIVATE_LIMITED",
            premises_type="INDUSTRIAL_AREA",
            flexible_attributes={"water_discharge_required": "true"}
        )
        business = await BusinessService.create_business(db, owner.id, biz_schema)
        print(f"[SUCCESS] 2. Business profile created: {business.name}")

        # 4. Generate Roadmap
        roadmap = await WorkflowService.generate_roadmap(db, business.id)
        fire_app = next((a for a in roadmap if a.rule_code == "FIRE_NOC"), None)
        fssai_app = next((a for a in roadmap if a.rule_code == "FSSAI_LICENSE"), None)
        assert fire_app and fssai_app

        # 5. Test Module 12: Schedule Inspection
        now = datetime.utcnow()
        sched_schema = InspectionScheduleSchema(
            approval_id=fire_app.id,
            title="Maharashtra Fire Services On-Site Safety Inspection",
            scheduled_date=now + timedelta(days=3),
            location_address="Plot B-14, MIDC Bhosari, Pune",
            officer_id=officer.id
        )
        inspection = await InspectionService.schedule_inspection(db, sched_schema)
        print(f"[SUCCESS] 3. Fire NOC Inspection Scheduled:")
        print(f"           - Title: {inspection.title}")
        print(f"           - Scheduled Date: {inspection.scheduled_date}")
        print(f"           - Status: {inspection.status.value}")
        assert inspection.status == InspectionStatus.SCHEDULED

        updated_fire_app = await WorkflowService.get_approval_by_id(db, fire_app.id)
        assert updated_fire_app.status == ApprovalStatus.INSPECTION_PENDING
        print(f"[SUCCESS] 4. Approval status updated to: {updated_fire_app.status.value}")

        # 6. Test Module 12: Reschedule Inspection
        resched_schema = InspectionRescheduleSchema(
            new_scheduled_date=now + timedelta(days=5),
            reason="Inspector delayed due to emergency monsoon fire response duty."
        )
        rescheduled_inspection = await InspectionService.reschedule_inspection(db, inspection.id, resched_schema)
        print(f"[SUCCESS] 5. Inspection Rescheduled to: {rescheduled_inspection.scheduled_date}")

        # 7. Test Module 12: Submit Inspection Report & Auto-Approve
        report_schema = InspectionReportSchema(
            status=InspectionStatus.COMPLETED,
            inspector_notes="Inspected premises MIDC Bhosari. Dual fire hydrants and 500L water tank verified.",
            findings_summary="All statutory Maharashtra Fire Prevention standards met cleanly.",
            checklist_results=[
                {"check": "Fire Extinguishers ISI Certified", "passed": True},
                {"check": "Emergency Exits Unobstructed", "passed": True},
                {"check": "Fire Alarm Panel Operational", "passed": True}
            ]
        )
        completed_inspection = await InspectionService.submit_inspection_report(db, inspection.id, report_schema)
        print(f"[SUCCESS] 6. Inspection Report Submitted & Approved:")
        print(f"           - Inspection Status: {completed_inspection.status.value}")
        
        final_fire_app = await WorkflowService.get_approval_by_id(db, fire_app.id)
        print(f"           - Fire NOC Approval Status: {final_fire_app.status.value}")
        assert final_fire_app.status == ApprovalStatus.APPROVED

        # 8. Test Module 13: Raise Grievance Ticket
        grievance_schema = GrievanceCreateSchema(
            business_id=business.id,
            approval_id=fssai_app.id,
            title="FSSAI License SLA Delay & Officer Unresponsiveness",
            description="Application submitted 20 days ago but no officer assigned yet on FoSCoS portal.",
            category=GrievanceCategory.SLA_BREACH,
            priority=GrievancePriority.HIGH,
            department="Food Safety and Standards Authority of India (FSSAI)"
        )
        grievance = await GrievanceService.create_grievance(db, owner.id, grievance_schema)
        print(f"[SUCCESS] 7. Grievance Ticket Created:")
        print(f"           - Ticket ID: {grievance.id}")
        print(f"           - Priority: {grievance.priority.value}")
        print(f"           - Initial Escalation Level: {grievance.escalation_level} (Level 1 Nodal)")
        print(f"           - Resolution Deadline: {grievance.resolution_deadline}")
        assert grievance.escalation_level == 1

        # 9. Test Module 13: Assign Officer
        assigned_grievance = await GrievanceService.assign_officer(db, grievance.id, officer.id)
        print(f"[SUCCESS] 8. Grievance Assigned to Officer ID: {assigned_grievance.assigned_officer_id}")
        assert assigned_grievance.status == GrievanceStatus.ASSIGNED

        # 10. Test Module 13: Automatic Multi-Tier Escalation Engine
        # Simulate passed resolution deadline
        assigned_grievance.resolution_deadline = now - timedelta(hours=5)
        db.add(assigned_grievance)
        await db.commit()

        escalated_list = await GrievanceService.check_and_escalate_grievances(db, business.id)
        escalated_grievance = next((g for g in escalated_list if g.id == grievance.id), None)
        print(f"[SUCCESS] 9. Automatic Multi-Tier Escalation Engine Triggered:")
        print(f"           - New Status: {escalated_grievance.status.value}")
        print(f"           - Escalation Level: Level {escalated_grievance.escalation_level} (Regional Senior Inspector)")
        print(f"           - Escalation History Entries: {len(escalated_grievance.escalation_history)}")
        assert escalated_grievance.escalation_level == 2
        assert escalated_grievance.status == GrievanceStatus.ESCALATED

        # 11. Test Module 13: Resolve Grievance
        resolved_grievance = await GrievanceService.resolve_grievance(
            db, grievance.id, "Nodal Officer dispatched FSSAI license directly via G2B gateway.", officer.id
        )
        print(f"[SUCCESS] 10. Grievance Resolved Cleanly:")
        print(f"           - Status: {resolved_grievance.status.value}")
        print(f"           - Resolution Notes: {resolved_grievance.resolution_notes}")
        assert resolved_grievance.status == GrievanceStatus.RESOLVED

        print("==================================================")
        print(" MODULE 12 & 13 ALL TESTS PASSED CLEANLY!         ")
        print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_inspections_grievances_tests())
