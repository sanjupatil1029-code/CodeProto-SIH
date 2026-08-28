import asyncio
import os
import sys
import uuid
import datetime
from io import BytesIO
from starlette.datastructures import Headers

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.core import database
from app.schemas.auth import UserRegister
from app.schemas.business import BusinessCreate
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService
from app.services.document_service import DocumentService
from app.services.security_scanner import SecurityScanner
from app.services.validation_service import DocumentValidationService
from app.schemas.document_validation import IssueType, IssueSeverity
from fastapi import UploadFile


async def run_validation_tests():
    print("==================================================")
    print("  MODULE 7: DOCUMENT VALIDATION ENGINE TEST SUITE ")
    print("==================================================")

    # 1. Initialize DB
    db_ok = await database.check_and_fallback_db()
    assert db_ok, "Database connection failed!"
    await database.init_db()
    print("[SUCCESS] 1. Database initialized.")

    # 2. Test File & Magic Bytes Scanner
    fake_exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00Fake Executable Header disguised as PDF"
    ok, msg = SecurityScanner.validate_file_magic_bytes(fake_exe_bytes, "application/pdf", "fake_invoice.pdf")
    assert not ok
    print(f"[SUCCESS] 2. Magic Bytes Scanner detected disguised executable: {msg}")

    # 3. Test Security Payload Scanner
    script_bytes = b"%PDF-1.4\n<script>alert('malicious_payload')</script>\n"
    safe, flags = SecurityScanner.scan_security_risks(script_bytes, "document_with_script.pdf")
    assert not safe
    print(f"[SUCCESS] 3. Security Payload Scanner flagged script payload: {flags[0]}")

    async with database.SessionLocal() as db:
        # 4. Create User & Business Profile located in PUNE, MAHARASHTRA
        test_email = f"validation_owner_{uuid.uuid4().hex[:6]}@example.com"
        user = await AuthService.register_user(
            db,
            UserRegister(
                email=test_email,
                password="SecurePassword123!",
                full_name="Validation Test Owner"
            )
        )

        biz_schema = BusinessCreate(
            name="Pune Bakers & Food Processing Pvt Ltd",
            sector="FOOD_PROCESSING",
            sub_sector="BAKERY_PRODUCTS",
            state="Maharashtra",
            district="Pune",
            city="Pune",  # BUSINESS ADDRESS IS PUNE
            investment_amount=15000000.0,
            employee_count=25,
            expected_turnover=3500000.0,
            operational_stage="REGISTERED",
            ownership_type="PRIVATE_LIMITED",
            premises_type="RENTED",
            flexible_attributes={"water_discharge_required": "true"}
        )
        business = await BusinessService.create_business(db, user.id, biz_schema)
        print(f"[SUCCESS] 4. Business profile registered in City: '{business.city}', District: '{business.district}' (ID: {business.id})")

        # 5. Upload Rental Agreement with ADDRESS IN MUMBAI (Cross-Document Inconsistency Example!)
        mumbai_rent_agreement = (
            b"%PDF-1.4\n"
            b"RENTAL AGREEMENT AND LEASE DEED\n"
            b"LESSOR: MUMBAI COMMERCIAL PROPERTIES LTD\n"
            b"LESSEE: PUNE BAKERS AND FOOD PROCESSING PVT LTD\n"
            b"PREMISES ADDRESS: PLOT 45, BANDRA KURLA COMPLEX, MUMBAI, MAHARASHTRA 400051\n"
            b"MONTHLY RENT: RS 85,000\n"
        )
        rent_file = UploadFile(
            filename="rent_agreement_mumbai.pdf",
            file=BytesIO(mumbai_rent_agreement),
            headers=Headers({"content-type": "application/pdf"})
        )

        rent_res = await DocumentService.upload_document(
            db=db,
            business_id=business.id,
            uploaded_by=user.id,
            file=rent_file,
            document_type="RENT_AGREEMENT"
        )
        rent_doc = rent_res.document
        print(f"[SUCCESS] 5. Uploaded Rental Agreement: ID {rent_doc.id}")

        # 6. Upload PAN Card & GST Certificate with PAN Mismatch
        pan_content = (
            b"%PDF-1.4\nINCOME TAX DEPARTMENT\nPERMANENT ACCOUNT NUMBER: ABCDE1234F\n"
            b"NAME: PUNE BAKERS AND FOOD PROCESSING PVT LTD\n"
        )
        pan_file = UploadFile(
            filename="pan_card.pdf",
            file=BytesIO(pan_content),
            headers=Headers({"content-type": "application/pdf"})
        )
        await DocumentService.upload_document(db, business.id, user.id, pan_file, "PAN_CARD")

        gst_mismatch_content = (
            b"GOVERNMENT OF INDIA - GOODS AND SERVICES TAX\n"
            b"GSTIN: 27XYZAB9876Q1Z5\n"  # 15-char GSTIN with embedded PAN XYZAB9876Q, mismatching ABCDE1234F!
            b"LEGAL NAME: PUNE BAKERS AND FOOD PROCESSING PVT LTD\n"
        )
        gst_file = UploadFile(
            filename="gst_cert.pdf",
            file=BytesIO(gst_mismatch_content),
            headers=Headers({"content-type": "application/pdf"})
        )
        await DocumentService.upload_document(db, business.id, user.id, gst_file, "GST_CERTIFICATE")

        # 7. Run Full Vault Validation Report
        report = await DocumentValidationService.generate_vault_validation_report(db, business.id)

        print("\n==================================================")
        print("        DOCUMENT VALIDATION ENGINE REPORT         ")
        print("==================================================")
        print(f"Business Name:           {report.business_name}")
        print(f"Overall Valid:           {report.overall_valid}")
        print(f"Vault Health Score:      {report.vault_health_score}/100")
        print(f"Total Documents Checked: {report.total_documents_checked}")
        print(f"Total Issues Found:      {report.total_issues_found}")

        print("\n--- Cross-Document Inconsistencies Detected ---")
        address_mismatch_found = False
        pan_mismatch_found = False

        for issue in report.cross_doc_inconsistencies:
            print(f"[{issue.severity.value}] {issue.issue_type.value}: {issue.message}")
            print(f"    Expected: {issue.expected_value} | Actual: {issue.actual_value}")
            print(f"    Affected Approvals: {', '.join(issue.affected_approvals)}")

            if issue.issue_type == IssueType.ADDRESS_MISMATCH:
                address_mismatch_found = True
                assert "Pune" in issue.expected_value
                assert "Mumbai" in issue.actual_value
                assert "FSSAI_LICENSE" in issue.affected_approvals

            if issue.issue_type == IssueType.PAN_GSTIN_MISMATCH:
                pan_mismatch_found = True
                assert "GST_REGISTRATION" in issue.affected_approvals

        assert address_mismatch_found, "Address Mismatch (Pune vs Mumbai) was not detected!"
        assert pan_mismatch_found, "PAN vs GSTIN Mismatch was not detected!"

        print("\n==================================================")
        print("    MODULE 7 VALIDATION TESTS PASSED CLEANLY!     ")
        print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_validation_tests())
