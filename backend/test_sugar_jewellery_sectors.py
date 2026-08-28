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
from app.models.auth import UserRole
from app.models.workflows import ApprovalStatus
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService
from app.services.workflow_service import WorkflowService
from app.services.rule_engine_service import RuleEngineService


async def run_sugar_jewellery_tests():
    print("==================================================")
    print(" SUGAR FACTORY & JEWELLERY SHOP SECTORS TEST SUITE")
    print("==================================================")

    # 1. Init Database & Seed Rules
    db_ok = await database.check_and_fallback_db()
    assert db_ok, "Database connection failed!"
    await database.init_db()
    
    async with database.SessionLocal() as db:
        await RuleEngineService.seed_default_rules(db)
    print("[SUCCESS] 1. Database initialized & rules seeded.")

    async with database.SessionLocal() as db:
        # 2. Register Owner
        owner_email = f"sector_owner_{uuid.uuid4().hex[:6]}@example.com"
        owner = await AuthService.register_user(
            db, UserRegister(email=owner_email, password="Password123!", full_name="Multi-Industry Entrepreneur")
        )
        await db.commit()

        # ==================================================
        # TEST 1: SUGAR FACTORY SECTOR (19 STEPS)
        # ==================================================
        print("\n--- TESTING SECTOR 1: SUGAR FACTORY (19 STATUTORY STEPS) ---")
        sugar_biz_schema = BusinessCreate(
            name="Sanjupatil Integrated Sugar Industries Ltd",
            sector="SUGAR_FACTORY",
            sub_sector="SUGAR_MILL_ETHANOL",
            state="Karnataka",
            district="Belagavi",
            city="Belagavi",
            investment_amount=1500000000.0,  # ₹150 Crores
            employee_count=450,
            expected_turnover=2500000000.0,  # ₹250 Crores
            operational_stage="REGISTERED",
            ownership_type="PUBLIC_LIMITED",
            premises_type="INDUSTRIAL_AREA"
        )
        sugar_biz = await BusinessService.create_business(db, owner.id, sugar_biz_schema)
        print(f"[SUCCESS] Sugar Factory Business Created: {sugar_biz.name}")

        sugar_roadmap = await WorkflowService.generate_roadmap(db, sugar_biz.id)
        print(f"[SUCCESS] Sugar Factory Roadmap Generated: {len(sugar_roadmap)} Statutory Approvals (Expected 19 steps)")
        assert len(sugar_roadmap) == 19, f"Expected 19 steps for Sugar Factory, got {len(sugar_roadmap)}"

        # Verify exact sequence
        print("          Sugar Factory Approval Steps Breakdown:")
        for idx, app in enumerate(sugar_roadmap, 1):
            print(f"          {idx:02d}. [{app.rule_code}] {app.name} | Status: {app.status.value} | SLA: {app.sla_days}d | Authority: {app.responsible_authority}")

        # Verify initial states: Step 1 (PAN/TAN) is READY, Step 19 (Release Order) is BLOCKED
        step_1 = next(a for a in sugar_roadmap if a.rule_code == "SUGAR_PAN_TAN")
        step_19 = next(a for a in sugar_roadmap if a.rule_code == "SUGAR_RELEASE_ORDER")
        assert step_1.status == ApprovalStatus.READY
        assert step_19.status == ApprovalStatus.BLOCKED

        # Simulate unlocking step 1
        await WorkflowService.update_approval_status(db, step_1.id, owner.id, UserRole.ENTREPRENEUR, ApprovalStatus.APPROVED)
        sugar_roadmap_updated = await WorkflowService.get_roadmap(db, sugar_biz.id)
        step_2 = next(a for a in sugar_roadmap_updated if a.rule_code == "SUGAR_NA_LAND")
        step_3 = next(a for a in sugar_roadmap_updated if a.rule_code == "SUGAR_IEM")
        assert step_2.status == ApprovalStatus.READY
        assert step_3.status == ApprovalStatus.READY
        print("[SUCCESS] Sugar Factory Step 1 Approved -> Steps 2 & 3 Unlocked to READY!")

        # ==================================================
        # TEST 2: JEWELLERY SHOP SECTOR (12 STEPS)
        # ==================================================
        print("\n--- TESTING SECTOR 2: JEWELLERY SHOP (12 STATUTORY STEPS) ---")
        jewel_biz_schema = BusinessCreate(
            name="Sanjupatil Heritage Gold & Diamonds",
            sector="JEWELLERY_SHOP",
            sub_sector="GOLD_DIAMOND_RETAIL",
            state="Maharashtra",
            district="Mumbai",
            city="Mumbai",
            investment_amount=80000000.0,  # ₹8 Crores
            employee_count=25,
            expected_turnover=150000000.0,  # ₹15 Crores
            operational_stage="REGISTERED",
            ownership_type="PRIVATE_LIMITED",
            premises_type="COMMERCIAL_SHOWROOM"
        )
        jewel_biz = await BusinessService.create_business(db, owner.id, jewel_biz_schema)
        print(f"[SUCCESS] Jewellery Shop Business Created: {jewel_biz.name}")

        jewel_roadmap = await WorkflowService.generate_roadmap(db, jewel_biz.id)
        print(f"[SUCCESS] Jewellery Shop Roadmap Generated: {len(jewel_roadmap)} Statutory Approvals (Expected 12 steps)")
        assert len(jewel_roadmap) == 12, f"Expected 12 steps for Jewellery Shop, got {len(jewel_roadmap)}"

        print("          Jewellery Shop Approval Steps Breakdown:")
        for idx, app in enumerate(jewel_roadmap, 1):
            print(f"          {idx:02d}. [{app.rule_code}] {app.name} | Status: {app.status.value} | SLA: {app.sla_days}d | Authority: {app.responsible_authority}")

        # Verify initial states: Step 1 (Entity Reg) is READY, Step 8 (BIS Jeweller) is BLOCKED
        j_step_1 = next(a for a in jewel_roadmap if a.rule_code == "JEWELLERY_ENTITY_REG")
        j_step_8 = next(a for a in jewel_roadmap if a.rule_code == "JEWELLERY_BIS_REG")
        assert j_step_1.status == ApprovalStatus.READY
        assert j_step_8.status == ApprovalStatus.BLOCKED

        # Simulate unlocking step 1
        await WorkflowService.update_approval_status(db, j_step_1.id, owner.id, UserRole.ENTREPRENEUR, ApprovalStatus.APPROVED)
        jewel_roadmap_updated = await WorkflowService.get_roadmap(db, jewel_biz.id)
        j_step_2 = next(a for a in jewel_roadmap_updated if a.rule_code == "JEWELLERY_PAN_BANK")
        j_step_3 = next(a for a in jewel_roadmap_updated if a.rule_code == "JEWELLERY_RENT_PROOF")
        assert j_step_2.status == ApprovalStatus.READY
        assert j_step_3.status == ApprovalStatus.READY
        print("[SUCCESS] Jewellery Shop Step 1 Approved -> Steps 2 & 3 Unlocked to READY!")

        print("\n==================================================")
        print(" SUGAR FACTORY & JEWELLERY SHOP ALL TESTS PASSED! ")
        print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_sugar_jewellery_tests())
