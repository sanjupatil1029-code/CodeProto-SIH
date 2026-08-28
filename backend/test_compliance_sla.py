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
from app.schemas.compliance import CertificateDatesUpdate
from app.models.workflows import ApprovalStatus
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService
from app.services.workflow_service import WorkflowService
from app.services.compliance_service import ComplianceService
from app.services.sla_engine_service import SLAEngineService


async def run_compliance_sla_tests():
    print("==================================================")
    print("   MODULE 10 & 11: COMPLIANCE & SLA ENGINE TESTS  ")
    print("==================================================")

    # 1. Init Database
    db_ok = await database.check_and_fallback_db()
    assert db_ok, "Database connection failed!"
    await database.init_db()
    print("[SUCCESS] 1. Database initialized.")

    async with database.SessionLocal() as db:
        # 2. Register Owner & Create Business Profile
        test_email = f"compliance_owner_{uuid.uuid4().hex[:6]}@example.com"
        user = await AuthService.register_user(
            db,
            UserRegister(
                email=test_email,
                password="SecurePassword123!",
                full_name="Compliance Manager"
            )
        )

        biz_schema = BusinessCreate(
            name="Apex Food Products India Pvt Ltd",
            sector="FOOD_PROCESSING",
            sub_sector="DAIRY_PROCESSING",
            state="Maharashtra",
            district="Pune",
            city="Pune",
            investment_amount=40000000.0,
            employee_count=60,
            expected_turnover=8000000.0,
            operational_stage="REGISTERED",
            ownership_type="PRIVATE_LIMITED",
            premises_type="INDUSTRIAL_AREA",
            flexible_attributes={"water_discharge_required": "true"}
        )
        business = await BusinessService.create_business(db, user.id, biz_schema)
        print(f"[SUCCESS] 2. Business Profile created: {business.name} (ID: {business.id})")

        # 3. Generate Roadmap Approvals
        roadmap = await WorkflowService.generate_roadmap(db, business.id)
        print(f"[SUCCESS] 3. Roadmap generated with {len(roadmap)} approval records.")

        fssai_app = next((a for a in roadmap if a.rule_code == "FSSAI_LICENSE"), None)
        fire_app = next((a for a in roadmap if a.rule_code == "FIRE_NOC"), None)
        water_app = next((a for a in roadmap if a.rule_code == "WATER_CONSENT"), None)
        assert fssai_app and fire_app and water_app

        # 4. Test Module 10: Expiration & Certificate Date Assignment
        now = datetime.utcnow()
        # Set FSSAI Certificate issued 350 days ago, expiring in 15 days (Trigger: RENEWAL_DUE)
        fssai_dates = CertificateDatesUpdate(
            issue_date=now - timedelta(days=350),
            expiry_date=now + timedelta(days=15),
            renewal_reminder_days=30
        )
        updated_fssai = await ComplianceService.update_certificate_dates(db, fssai_app.id, fssai_dates)
        print(f"[SUCCESS] 4. FSSAI License Certificate dates updated:")
        print(f"           - Expiry Date: {updated_fssai.expiry_date.strftime('%Y-%m-%d')}")
        print(f"           - Renewal Status: {updated_fssai.renewal_status}")
        assert updated_fssai.renewal_status == "RENEWAL_DUE"

        # Set Fire NOC Certificate issued 360 days ago, expiring in 5 days (Trigger: CRITICAL_RENEWAL)
        fire_dates = CertificateDatesUpdate(
            issue_date=now - timedelta(days=360),
            expiry_date=now + timedelta(days=5),
            renewal_reminder_days=30
        )
        updated_fire = await ComplianceService.update_certificate_dates(db, fire_app.id, fire_dates)
        print(f"[SUCCESS] 5. Fire NOC Certificate dates updated:")
        print(f"           - Expiry Date: {updated_fire.expiry_date.strftime('%Y-%m-%d')}")
        print(f"           - Renewal Status: {updated_fire.renewal_status}")
        assert updated_fire.renewal_status == "CRITICAL_RENEWAL"

        # 5. Evaluate Business Renewals Summary
        renewals_summary = await ComplianceService.evaluate_business_renewals(db, business.id)
        print(f"[SUCCESS] 6. Business Compliance Renewals Summary:")
        print(f"           - Total Licenses: {renewals_summary.total_licenses}")
        print(f"           - Up To Date: {renewals_summary.up_to_date_count}")
        print(f"           - Renewal Due: {renewals_summary.renewal_due_count}")
        print(f"           - Critical Renewal: {renewals_summary.critical_renewal_count}")
        assert renewals_summary.renewal_due_count >= 1
        assert renewals_summary.critical_renewal_count >= 1

        # 6. Test Module 11: SLA Calculation & Bottleneck Detection
        # Simulate active applications with artificial past start times
        # Water Consent started 25 days ago with 30-day SLA (25/30 = 83.3% -> SLA_WARNING)
        water_app.status = ApprovalStatus.IN_PROGRESS
        water_app.started_at = now - timedelta(days=25)
        water_app.sla_days = 30
        water_app.sla_deadline = water_app.started_at + timedelta(days=30)
        db.add(water_app)

        # Fire NOC started 40 days ago with 15-day SLA (40/15 = 266% -> SLA_BREACHED)
        fire_app.status = ApprovalStatus.UNDER_REVIEW
        fire_app.started_at = now - timedelta(days=40)
        fire_app.sla_days = 15
        fire_app.sla_deadline = fire_app.started_at + timedelta(days=15)
        db.add(fire_app)

        await db.commit()

        # 7. Evaluate SLA & Bottleneck Analytics
        sla_analytics = await SLAEngineService.evaluate_business_slas(db, business.id)
        print(f"[SUCCESS] 7. SLA & Bottleneck Analytics Evaluated:")
        print(f"           - Overall SLA Health: {sla_analytics.overall_sla_health_percent}%")
        print(f"           - Total Active: {sla_analytics.total_active_applications}")
        print(f"           - On Track: {sla_analytics.on_track_count}")
        print(f"           - SLA Warning (>=80%): {sla_analytics.warning_count}")
        print(f"           - SLA Breached (>=100%): {sla_analytics.breached_count}")
        assert sla_analytics.warning_count >= 1 or sla_analytics.breached_count >= 1

        print(f"[SUCCESS] 8. Department Bottleneck Breakdown:")
        for dept in sla_analytics.department_bottlenecks:
            print(f"           - Authority: '{dept.authority}' | In Progress: {dept.in_progress_count} | Breached: {dept.sla_breached_count} | Risk: {dept.bottleneck_risk_level}")

        print("==================================================")
        print("  MODULE 10 & 11 ALL TESTS PASSED CLEANLY!       ")
        print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_compliance_sla_tests())
