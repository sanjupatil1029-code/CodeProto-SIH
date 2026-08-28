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
from app.models.notification import NotificationEventType, NotificationSeverity
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService
from app.services.workflow_service import WorkflowService
from app.services.notification_service import NotificationService
from app.services.audit_service import AuditService


async def run_notifications_audit_tests():
    print("==================================================")
    print(" MODULE 16 & 17: NOTIFICATION & AUDIT LOG TESTS")
    print("==================================================")

    # 1. Init Database
    db_ok = await database.check_and_fallback_db()
    assert db_ok, "Database connection failed!"
    await database.init_db()
    print("[SUCCESS] 1. Database initialized.")

    async with database.SessionLocal() as db:
        # 2. Register Test User & Business Profile
        user_email = f"notif_owner_{uuid.uuid4().hex[:6]}@example.com"
        owner = await AuthService.register_user(
            db, UserRegister(email=user_email, password="Password123!", full_name="Compliance Manager")
        )
        await db.commit()

        biz_schema = BusinessCreate(
            name="Sanjupatil High-Tech Agro Processing Pvt Ltd",
            sector="FOOD_PROCESSING",
            sub_sector="DAIRY_PROCESSING",
            state="Maharashtra",
            district="Pune",
            city="Pune",
            investment_amount=50000000.0,
            employee_count=100,
            expected_turnover=120000000.0,
            operational_stage="REGISTERED",
            ownership_type="PRIVATE_LIMITED",
            premises_type="MIDC_PLOT"
        )
        business = await BusinessService.create_business(db, owner.id, biz_schema)
        print(f"[SUCCESS] 2. Business profile created: {business.name}")

        # 3. Log Audit Event for Business Creation (Module 17)
        audit_1 = await AuditService.log_audit_event(
            db=db,
            action="BUSINESS_CREATED",
            resource_type="Business",
            resource_id=str(business.id),
            actor_id=owner.id,
            actor_role="ENTREPRENEUR",
            old_value={},
            new_value={"name": business.name, "sector": business.sector, "state": business.state},
            ip_address="127.0.0.1"
        )
        print(f"[SUCCESS] 3. Business Creation Audit Log appended (ID: {audit_1.audit_id}):")
        print(f"           - Action: {audit_1.action}")
        print(f"           - Actor: {audit_1.actor_role} ({audit_1.actor_id})")

        # 4. Generate Workflow Roadmap & Log Status Audit Change
        roadmap = await WorkflowService.generate_roadmap(db, business.id)
        fssai_app = next((a for a in roadmap if a.rule_code == "FSSAI_LICENSE"), None)
        assert fssai_app

        audit_2 = await AuditService.log_audit_event(
            db=db,
            action="APPROVAL_STATUS_CHANGED",
            resource_type="BusinessApproval",
            resource_id=str(fssai_app.id),
            actor_id=owner.id,
            actor_role="ENTREPRENEUR",
            old_value={"status": "NOT_STARTED", "sla_days": 30},
            new_value={"status": "IN_PROGRESS", "sla_days": 30},
            ip_address="127.0.0.1"
        )
        print(f"[SUCCESS] 4. Approval Status Audit Log appended (ID: {audit_2.audit_id}).")

        # 5. Dispatch Event Notifications (Module 16)
        n1 = await NotificationService.create_notification(
            db=db,
            user_id=owner.id,
            event_type=NotificationEventType.APPLICATION_STATUS_CHANGED,
            severity=NotificationSeverity.INFO,
            title="FSSAI License Application Started",
            message="Your FSSAI Food Business License application status has transitioned to IN_PROGRESS.",
            resource_type="BusinessApproval",
            resource_id=str(fssai_app.id),
            send_email=True
        )

        n2 = await NotificationService.create_notification(
            db=db,
            user_id=owner.id,
            event_type=NotificationEventType.SLA_WARNING,
            severity=NotificationSeverity.WARNING,
            title="SLA Warning: 7 Days Remaining for Fire NOC",
            message="Fire NOC approval processing SLA deadline is approaching in 7 days.",
            resource_type="BusinessApproval",
            resource_id=str(fssai_app.id),
            send_email=True
        )

        n3 = await NotificationService.create_notification(
            db=db,
            user_id=owner.id,
            event_type=NotificationEventType.REGULATION_UPDATED,
            severity=NotificationSeverity.CRITICAL,
            title="Official Gazette Update: FSSAI Rule Version 2.0 Deployed",
            message="FSSAI License processing window has been reduced to 15 days under Gazette Notification 2026.",
            resource_type="ApprovalRule",
            resource_id="FSSAI_LICENSE",
            send_email=True
        )
        print(f"[SUCCESS] 5. 3 Event-Based Notifications Dispatched (In-App & Email Abstraction):")
        print(f"           - N1: '{n1.title}' (Sent Email: {n1.email_sent})")
        print(f"           - N2: '{n2.title}' (Sent Email: {n2.email_sent})")
        print(f"           - N3: '{n3.title}' (Sent Email: {n3.email_sent})")

        # 6. Verify User In-App Notification Feed & Unread Count
        feed_before = await NotificationService.get_user_notifications(db, owner.id, unread_only=True)
        print(f"[SUCCESS] 6. Unread Notification Feed Verified:")
        print(f"           - Total Count: {feed_before.total_count}")
        print(f"           - Unread Count: {feed_before.unread_count}")
        assert feed_before.unread_count == 3

        # 7. Mark Single & All Notifications as Read
        await NotificationService.mark_as_read(db, n1.id, owner.id)
        marked_count = await NotificationService.mark_all_read(db, owner.id)
        print(f"[SUCCESS] 7. Marked Notifications as Read (Marked {marked_count} unread).")

        feed_after = await NotificationService.get_user_notifications(db, owner.id, unread_only=True)
        assert feed_after.unread_count == 0
        print(f"[SUCCESS] 8. Unread Feed Count is now 0.")

        # 8. Query Audit Log History for Resource (Module 17)
        audit_history = await AuditService.get_audit_logs(
            db=db,
            resource_type="BusinessApproval",
            resource_id=str(fssai_app.id)
        )
        print(f"[SUCCESS] 9. Query Resource Audit Log Trail (Found {audit_history.total_count} records):")
        for log in audit_history.logs:
            print(f"           - Action: {log.action} | Timestamp: {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | Diff: {log.old_value} -> {log.new_value}")
        assert audit_history.total_count >= 1

        print("==================================================")
        print(" MODULE 16 & 17 ALL TESTS PASSED CLEANLY!         ")
        print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_notifications_audit_tests())
