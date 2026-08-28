import asyncio
import os
import sys
import uuid
import datetime
from io import BytesIO

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from app.core import database
from app.models.auth import User, UserRole
from app.models.business import Business
from app.schemas.auth import UserRegister
from app.schemas.business import BusinessCreate
from app.schemas.document import DocumentVerifyRequest
from app.services.auth_service import AuthService
from app.services.business_service import BusinessService
from app.services.document_service import DocumentService
from app.services.storage_service import StorageService
from app.services.ocr_service import OCRService
from fastapi import UploadFile
from starlette.datastructures import Headers


async def run_tests():
    print("==================================================")
    print("    MODULE 6: SMART DOCUMENT VAULT TEST SUITE     ")
    print("==================================================")

    # 1. Initialize Database
    db_ok = await database.check_and_fallback_db()
    assert db_ok, "Database connection failed!"
    await database.init_db()
    print("[SUCCESS] 1. Database initialized and tables verified.")

    async with database.SessionLocal() as db:
        # 2. Setup Test User & Business Profile
        test_email = f"vault_owner_{uuid.uuid4().hex[:6]}@example.com"
        user = await AuthService.register_user(
            db,
            UserRegister(
                email=test_email,
                password="SecurePassword123!",
                full_name="Vault Test Owner"
            )
        )
        print(f"[SUCCESS] 2. User created: {user.email} (ID: {user.id})")

        biz_schema = BusinessCreate(
            name="Apex Foods & Beverages Pvt Ltd",
            sector="FOOD_PROCESSING",
            sub_sector="BEVERAGE_MANUFACTURING",
            state="Maharashtra",
            district="Pune",
            city="Pune",
            investment_amount=25000000.0,  # 2.5 Cr
            employee_count=35,
            expected_turnover=4500000.0,   # 45 Lakhs
            operational_stage="REGISTERED",
            ownership_type="PRIVATE_LIMITED",
            premises_type="MIDC_PLOT",
            flexible_attributes={"water_discharge_required": "true"}
        )
        business = await BusinessService.create_business(db, user.id, biz_schema)
        print(f"[SUCCESS] 3. Business created: {business.name} (ID: {business.id})")

        # 3. Test File Upload 1 - PAN Card (PDF format)
        pan_content = (
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"INCOME TAX DEPARTMENT\nGOVT OF INDIA\nPERMANENT ACCOUNT NUMBER: ABCDE1234F\n"
            b"NAME: APEX FOODS AND BEVERAGES PVT LTD\nISSUE DATE: 15/01/2022\n"
        )
        file1 = UploadFile(
            filename="pan_card_apex.pdf",
            file=BytesIO(pan_content),
            headers=Headers({"content-type": "application/pdf"})
        )

        res1 = await DocumentService.upload_document(
            db=db,
            business_id=business.id,
            uploaded_by=user.id,
            file=file1,
            document_type="PAN_CARD"
        )
        doc1 = res1.document
        print(f"[SUCCESS] 4. Uploaded PAN Card v{doc1.version}: ID {doc1.id}")
        print(f"           - Storage Key: {doc1.storage_key}")
        print(f"           - File Hash: {doc1.file_hash}")
        print(f"           - OCR Classification Confidence: {doc1.classification_confidence}")
        print(f"           - Extracted Data: {doc1.extracted_data}")
        print(f"           - Verification Status: {doc1.verification_status}")
        assert doc1.version == 1
        assert doc1.is_latest == True
        assert doc1.extracted_data.get("document_number") == "ABCDE1234F"

        # 4. Test File Upload 2 - Document Versioning (Upload updated PAN Card)
        pan_v2_content = (
            b"%PDF-1.4\nUPDATED PAN CARD FOR APEX FOODS\nPERMANENT ACCOUNT NUMBER: ABCDE1234F\n"
            b"NAME: APEX FOODS & BEVERAGES PRIVATE LIMITED\nISSUE DATE: 20/08/2026\n"
        )
        file2 = UploadFile(
            filename="pan_card_apex_v2.pdf",
            file=BytesIO(pan_v2_content),
            headers=Headers({"content-type": "application/pdf"})
        )

        res2 = await DocumentService.upload_document(
            db=db,
            business_id=business.id,
            uploaded_by=user.id,
            file=file2,
            document_type="PAN_CARD"
        )
        doc2 = res2.document
        print(f"[SUCCESS] 5. Uploaded Document Version 2 for PAN Card: ID {doc2.id}")
        print(f"           - Version: {doc2.version}")
        print(f"           - Parent Document ID: {doc2.parent_document_id}")
        assert doc2.version == 2
        assert doc2.is_latest == True
        assert doc2.parent_document_id == doc1.id

        # Verify old version 1 is marked is_latest=False
        old_doc1 = await DocumentService.get_document_by_id(db, doc1.id)
        assert old_doc1.is_latest == False
        print(f"[SUCCESS] 6. Confirmed v1 (ID: {old_doc1.id}) archived (is_latest={old_doc1.is_latest}).")

        # 5. Upload GST Certificate
        gst_content = (
            b"GOVERNMENT OF INDIA - GOODS AND SERVICES TAX\n"
            b"REGISTRATION CERTIFICATE\n"
            b"GSTIN: 27ABCDE1234F1Z5\nLEGAL NAME: APEX FOODS AND BEVERAGES PVT LTD\n"
            b"VALID FROM: 01/04/2022\nEXPIRY DATE: 31/12/2030\n"
        )
        file3 = UploadFile(
            filename="gst_certificate.pdf",
            file=BytesIO(gst_content),
            headers=Headers({"content-type": "application/pdf"})
        )

        res3 = await DocumentService.upload_document(
            db=db,
            business_id=business.id,
            uploaded_by=user.id,
            file=file3,
            document_type="GST_IN"
        )
        doc3 = res3.document
        print(f"[SUCCESS] 7. Uploaded GST Certificate: ID {doc3.id}, Number: {doc3.extracted_data.get('document_number')}")
        assert doc3.extracted_data.get("document_number") == "27ABCDE1234F1Z5"

        # 6. Test Manual Officer Verification
        verified_doc = await DocumentService.verify_document(
            db=db,
            document_id=doc2.id,
            schema=DocumentVerifyRequest(
                verification_status="VERIFIED",
                verification_notes="Verified by Officer against Govt Income Tax Database."
            )
        )
        print(f"[SUCCESS] 8. Officer verified document {verified_doc.id}: Status = {verified_doc.verification_status}")
        assert verified_doc.verification_status == "VERIFIED"

        # 7. Test Signed URL Generation & Verification
        token, expires_at = StorageService.generate_signed_token(doc2.id, user.id, expires_in_seconds=120)
        payload = StorageService.verify_signed_token(token)
        print(f"[SUCCESS] 9. Generated & Verified HMAC Signed URL Token for document {doc2.id}")
        assert payload["sub"] == str(doc2.id)

        # 8. Test Secure File Retrieval from Storage
        read_bytes = StorageService.read_file(doc2.storage_key)
        assert read_bytes == pan_v2_content
        print(f"[SUCCESS] 10. Retrieved raw file content from Storage key. Length: {len(read_bytes)} bytes.")

        # 9. Test Business Vault Compliance Check
        compliance = await DocumentService.check_business_vault_compliance(db, business.id)
        print(f"[SUCCESS] 11. Vault Compliance Calculated:")
        print(f"           - Total Required: {compliance.total_required}")
        print(f"           - Total Uploaded: {compliance.total_uploaded}")
        print(f"           - Total Verified: {compliance.total_verified}")
        print(f"           - Completion Percentage: {compliance.completion_percentage}%")
        print(f"           - Is Fully Compliant: {compliance.is_fully_compliant}")

        print("==================================================")
        print("    ALL MODULE 6 VAULT TESTS PASSED SUCCESSFULLY! ")
        print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_tests())
