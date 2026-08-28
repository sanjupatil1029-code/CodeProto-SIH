import asyncio
import os
import sys
import uuid
from datetime import datetime

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core import database
from app.schemas.auth import UserRegister
from app.schemas.business import BusinessCreate
from app.schemas.regulatory_update import RegulatoryUpdateCreateSchema
from app.models.auth import UserRole
from app.models.regulatory_update import UpdateStatus
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService
from app.services.workflow_service import WorkflowService
from app.services.scheme_matcher_service import SchemeMatcherService
from app.services.regulatory_update_service import RegulatoryUpdateService


async def run_schemes_regulatory_tests():
    print("==================================================")
    print(" MODULE 14 & 15: SCHEME MATCHER & REGULATORY TESTS")
    print("==================================================")

    # 1. Init Database
    db_ok = await database.check_and_fallback_db()
    assert db_ok, "Database connection failed!"
    await database.init_db()
    print("[SUCCESS] 1. Database initialized.")

    async with database.SessionLocal() as db:
        # 2. Register Admin & Business Owner
        admin_email = f"admin_reg_{uuid.uuid4().hex[:6]}@example.com"
        admin = await AuthService.register_user(
            db, UserRegister(email=admin_email, password="Password123!", full_name="System Admin")
        )
        admin.role = UserRole.ADMIN
        db.add(admin)

        owner_email = f"scheme_owner_{uuid.uuid4().hex[:6]}@example.com"
        owner = await AuthService.register_user(
            db, UserRegister(email=owner_email, password="Password123!", full_name="Food Business Owner")
        )
        await db.commit()

        # 3. Create Business Profile
        biz_schema = BusinessCreate(
            name="Sanjupatil Premium Fruit Processing Pvt Ltd",
            sector="FOOD_PROCESSING",
            sub_sector="FRUIT_JUICE_PROCESSING",
            state="Maharashtra",
            district="Pune",
            city="Pune",
            investment_amount=35000000.0,  # ₹3.5 Crores
            employee_count=50,
            expected_turnover=8000000.0,
            operational_stage="REGISTERED",
            ownership_type="PRIVATE_LIMITED",
            premises_type="MIDC_PLOT",
            flexible_attributes={"water_discharge_required": "true"}
        )
        business = await BusinessService.create_business(db, owner.id, biz_schema)
        print(f"[SUCCESS] 2. Business profile created: {business.name}")

        # 4. Generate Workflow Roadmap
        roadmap = await WorkflowService.generate_roadmap(db, business.id)
        fssai_app = next((a for a in roadmap if a.rule_code == "FSSAI_LICENSE"), None)
        assert fssai_app
        print(f"[SUCCESS] 3. Roadmap generated with FSSAI SLA: {fssai_app.sla_days} days.")

        # 5. Test Module 14: Scheme Matcher Engine
        scheme_matches = await SchemeMatcherService.match_schemes_for_business(db, business.id)
        print(f"[SUCCESS] 4. Government Scheme Matcher Evaluated:")
        print(f"           - Total Schemes Evaluated: {scheme_matches.total_schemes_evaluated}")
        print(f"           - Matched Count: {scheme_matches.matched_count}")
        print(f"           - Conditional Count: {scheme_matches.conditional_count}")
        print(f"           - Total Estimated Subsidy Benefit: INR {scheme_matches.total_potential_benefit:,.2f}")
        assert scheme_matches.matched_count >= 2

        print("[SUCCESS] 5. Matched Scheme Details:")
        for m in scheme_matches.matches:
            if m.match_status == "MATCHED":
                print(f"           - Scheme: '{m.name}' | Benefit: INR {m.estimated_benefit_amount:,.2f} | Portal: {m.official_portal_url}")
                assert len(m.required_documents) > 0

        # 6. Test Module 15: Propose Regulatory Update
        update_schema = RegulatoryUpdateCreateSchema(
            title="FSSAI Gazette Notification 2026: Fast-Track SLA & Water Quality Mandate",
            source_authority="Food Safety and Standards Authority of India (Central Ministry Gazette)",
            rule_code="FSSAI_LICENSE",
            summary="Fast-track SLA reduced from 30 days to 15 days for processed fruit units. Mandatory water discharge quality test report added.",
            extracted_changes={
                "sla_days": 15,
                "added_documents": ["WATER_TEST_REPORT"]
            },
            impact_summary="Reduces statutory processing window to 15 days; adds mandatory Water Quality Test Report to required document checklist."
        )
        prop_update = await RegulatoryUpdateService.propose_regulatory_update(db, update_schema)
        print(f"[SUCCESS] 6. Proposed Regulatory Update Created (ID: {prop_update.id}):")
        print(f"           - Title: {prop_update.title}")
        print(f"           - Status: {prop_update.status.value}")
        assert prop_update.status == UpdateStatus.DRAFT_PENDING_REVIEW

        # 7. Test Module 15: Admin Review Approval & Immutable Versioning
        approved_update = await RegulatoryUpdateService.review_regulatory_update(
            db, prop_update.id, approve=True, admin_user_id=admin.id, review_notes="Verified against official Government Gazette Notification No. 102/2026."
        )
        print(f"[SUCCESS] 7. Regulatory Update Reviewed & APPROVED by Admin:")
        print(f"           - Status: {approved_update.status.value}")
        print(f"           - Reviewed By: {approved_update.reviewed_by}")
        assert approved_update.status == UpdateStatus.APPROVED

        # 8. Verify Rule Version Upgrade (v1.0 -> v2.0)
        history = await RegulatoryUpdateService.get_rule_version_history(db, "FSSAI_LICENSE")
        print(f"[SUCCESS] 8. Rule Version Audit History ({history.versions_count} versions found):")
        for v in history.versions:
            print(f"           - Version: {v.rule_version} | Status: {v.status} | Is Latest: {v.is_latest} | SLA: {v.sla_days} days | Effective From: {v.effective_from.strftime('%Y-%m-%d %H:%M')}")

        latest_ver = next((v for v in history.versions if v.is_latest), None)
        old_ver = next((v for v in history.versions if not v.is_latest), None)
        assert latest_ver and old_ver
        assert latest_ver.rule_version == "2.0"
        assert latest_ver.sla_days == 15
        assert old_ver.status == "SUPERSEDED"

        # 9. Verify Affected Business Roadmap Auto-Update
        updated_fssai_app = await WorkflowService.get_approval_by_id(db, fssai_app.id)
        print(f"[SUCCESS] 9. Business Roadmap Auto-Updated to New Rule SLA:")
        print(f"           - Updated SLA Days: {updated_fssai_app.sla_days} days (Was 30 days)")
        print(f"           - Stage History Logs: {len(updated_fssai_app.stage_history)}")
        assert updated_fssai_app.sla_days == 15

        print("==================================================")
        print(" MODULE 14 & 15 ALL TESTS PASSED CLEANLY!         ")
        print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_schemes_regulatory_tests())
