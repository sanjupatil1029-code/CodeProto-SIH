import asyncio
import os
import sys
import uuid
import datetime

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core import database
from app.schemas.auth import UserRegister
from app.schemas.business import BusinessCreate
from app.adapters.factory import AdapterFactory
from app.models.workflows import ApprovalStatus, IntegrationMode
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService
from app.services.workflow_service import WorkflowService


async def run_adapter_tests():
    print("==================================================")
    print("  MODULE 8 & 9: WORKFLOW TRACKING & ADAPTER TESTS ")
    print("==================================================")

    # 1. Test Adapter Factory & Registry Resolution
    fssai_adapter = AdapterFactory.get_adapter("FSSAI_LICENSE")
    assert fssai_adapter.system_name == "FoSCoS (FSSAI)"
    assert fssai_adapter.integration_mode == IntegrationMode.PORTAL_HANDOFF
    assert fssai_adapter.get_official_portal_url() == "https://foscos.fssai.gov.in"
    print(f"[SUCCESS] 1. FSSAI Adapter resolved: {fssai_adapter.system_name} ({fssai_adapter.integration_mode.value}) -> {fssai_adapter.get_official_portal_url()}")

    gst_adapter = AdapterFactory.get_adapter("GST_REGISTRATION")
    assert gst_adapter.system_name == "GST Portal (CBIC)"
    assert gst_adapter.integration_mode == IntegrationMode.PUBLIC_API
    assert gst_adapter.get_official_portal_url() == "https://services.gst.gov.in"
    print(f"[SUCCESS] 2. GST Adapter resolved: {gst_adapter.system_name} ({gst_adapter.integration_mode.value}) -> {gst_adapter.get_official_portal_url()}")

    maitri_adapter = AdapterFactory.get_adapter("FIRE_NOC")
    assert maitri_adapter.system_name == "MAITRI Single Window (Maharashtra Govt)"
    assert maitri_adapter.integration_mode == IntegrationMode.PORTAL_HANDOFF
    assert maitri_adapter.get_official_portal_url() == "https://maitri.mahaonline.gov.in"
    print(f"[SUCCESS] 3. MAITRI Adapter resolved: {maitri_adapter.system_name} ({maitri_adapter.integration_mode.value}) -> {maitri_adapter.get_official_portal_url()}")

    # 2. Database Initialization
    db_ok = await database.check_and_fallback_db()
    assert db_ok, "Database connection failed!"
    await database.init_db()
    print("[SUCCESS] 4. Database initialized.")

    async with database.SessionLocal() as db:
        # 3. Create User & Business Profile
        test_email = f"workflow_owner_{uuid.uuid4().hex[:6]}@example.com"
        user = await AuthService.register_user(
            db,
            UserRegister(
                email=test_email,
                password="SecurePassword123!",
                full_name="Workflow Adapter Owner"
            )
        )

        biz_schema = BusinessCreate(
            name="Sanjupatil Foods & Beverages Pvt Ltd",
            sector="FOOD_PROCESSING",
            sub_sector="BEVERAGES",
            state="Maharashtra",
            district="Pune",
            city="Pune",
            investment_amount=30000000.0,
            employee_count=40,
            expected_turnover=5000000.0,
            operational_stage="REGISTERED",
            ownership_type="PRIVATE_LIMITED",
            premises_type="MIDC_PLOT",
            flexible_attributes={"water_discharge_required": "true"}
        )
        business = await BusinessService.create_business(db, user.id, biz_schema)
        print(f"[SUCCESS] 5. Business profile created: {business.name} (ID: {business.id})")

        # 4. Generate Workflow Roadmap
        roadmap = await WorkflowService.generate_roadmap(db, business.id)
        print(f"[SUCCESS] 6. Roadmap generated with {len(roadmap)} approval steps.")
        for item in roadmap:
            print(f"           - Step: {item.name} ({item.rule_code}) | Status: {item.status.value} | System: {item.external_system} | Mode: {item.integration_mode}")

        fssai_app = next((a for a in roadmap if a.rule_code == "FSSAI_LICENSE"), None)
        gst_app = next((a for a in roadmap if a.rule_code == "GST_REGISTRATION"), None)
        assert fssai_app is not None, "FSSAI_LICENSE not in roadmap"
        assert gst_app is not None, "GST_REGISTRATION not in roadmap"

        # 5. Test Module 8 & 9 Official Portal Handoff for FSSAI
        handoff_res = await WorkflowService.initiate_portal_handoff(db, fssai_app.id, user.id)
        print(f"[SUCCESS] 7. FSSAI Official Portal Handoff Initiated:")
        print(f"           - Status: {handoff_res.status.value}")
        print(f"           - System: {handoff_res.external_system}")
        print(f"           - Portal URL: {handoff_res.official_portal_url}")
        print(f"           - Instructions: {handoff_res.handoff_instructions}")
        assert handoff_res.status == ApprovalStatus.OFFICIAL_PORTAL_HANDOFF
        assert handoff_res.official_portal_url == "https://foscos.fssai.gov.in"

        # 6. Test Application Submission via Adapter Layer for GST
        submit_res = await WorkflowService.submit_workflow_application(db, gst_app.id, user.id)
        print(f"[SUCCESS] 8. GST Application Submitted via Government Adapter Layer:")
        print(f"           - Status: {submit_res.status.value}")
        print(f"           - External Reference ID (ARN): {submit_res.external_reference_id}")
        print(f"           - SLA Deadline: {submit_res.sla_deadline}")
        assert submit_res.status == ApprovalStatus.SUBMITTED
        assert submit_res.external_reference_id is not None
        assert "GST" in submit_res.external_reference_id or "AA" in submit_res.external_reference_id

        # 7. Test External Status Sync
        sync_res = await WorkflowService.sync_external_status(db, gst_app.id, user.id)
        print(f"[SUCCESS] 9. Status Synced from External GST System:")
        print(f"           - Current Status: {sync_res.current_status.value}")
        print(f"           - Remarks: {sync_res.remarks}")
        assert sync_res.current_status in [ApprovalStatus.SUBMITTED, ApprovalStatus.APPROVED, ApprovalStatus.IN_PROGRESS]

        # 8. Verify Stage History Audit Log
        updated_gst = await WorkflowService.get_approval_by_id(db, gst_app.id)
        print(f"[SUCCESS] 10. Stage History Log verified ({len(updated_gst.stage_history)} log entries):")
        for log_entry in updated_gst.stage_history:
            print(f"           - [{log_entry.get('timestamp', '')[:19]}] Status: {log_entry.get('status')} | Notes: {log_entry.get('notes', log_entry.get('sync_remarks', ''))}")
        assert len(updated_gst.stage_history) >= 2

        print("==================================================")
        print("    MODULE 8 & 9 ALL TESTS PASSED CLEANLY!       ")
        print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_adapter_tests())
