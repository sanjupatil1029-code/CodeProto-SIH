import uuid
import datetime
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.document import Document, VerificationStatus
from app.schemas.document_validation import (
    IssueType,
    IssueSeverity,
    ValidationErrorItem,
    DocumentValidationResult,
    VaultValidationReportOut,
)
from app.services.security_scanner import SecurityScanner
from app.services.ocr_service import OCRService
from app.services.rule_engine_service import RuleEngineService
from app.core.logging import logger

# Mapping of document validation failures to affected approval rules
APPROVAL_IMPACT_MAP = {
    IssueType.ADDRESS_MISMATCH: ["FSSAI_LICENSE", "FIRE_NOC", "WATER_CONSENT", "LOCAL_MUNICIPAL_NOC"],
    IssueType.NAME_MISMATCH: ["GST_REGISTRATION", "FSSAI_LICENSE", "WATER_CONSENT"],
    IssueType.PAN_GSTIN_MISMATCH: ["GST_REGISTRATION", "FSSAI_LICENSE"],
    IssueType.EXPIRED_DOCUMENT: ["FSSAI_LICENSE", "FIRE_NOC", "WATER_CONSENT"],
    IssueType.WRONG_DOCUMENT_TYPE: ["GST_REGISTRATION", "FSSAI_LICENSE", "FIRE_NOC", "WATER_CONSENT"],
    IssueType.INVALID_FILE: ["GST_REGISTRATION", "FSSAI_LICENSE", "FIRE_NOC", "WATER_CONSENT"],
    IssueType.VIRUS_SECURITY_RISK: ["ALL_APPROVALS"],
    IssueType.MISSING_REQUIRED_DOCUMENT: ["GST_REGISTRATION", "FSSAI_LICENSE", "FIRE_NOC", "WATER_CONSENT"]
}


class DocumentValidationService:

    @classmethod
    def validate_single_document(
        cls,
        file_bytes: bytes,
        filename: str,
        mime_type: str,
        expected_document_type: str,
        extracted_data: Optional[Dict[str, Any]] = None,
        classified_type: Optional[str] = None,
        confidence: float = 1.0,
        doc_id: Optional[uuid.UUID] = None
    ) -> DocumentValidationResult:
        """
        Runs Step 1 through Step 5 single-document validations:
        1. File Magic Bytes Check
        2. Virus & Security Scanner Payload Scan
        3. Wrong Document Type Classification Check
        4. Expiry Date Check
        5. Missing Mandatory Structured Fields
        """
        issues: List[ValidationErrorItem] = []

        # 1. File Magic Bytes Check
        magic_ok, magic_msg = SecurityScanner.validate_file_magic_bytes(file_bytes, mime_type, filename)
        if not magic_ok:
            issues.append(
                ValidationErrorItem(
                    issue_type=IssueType.INVALID_FILE,
                    severity=IssueSeverity.CRITICAL,
                    message=magic_msg,
                    field_name="file_header",
                    expected_value=f"Valid magic bytes for {mime_type}",
                    actual_value="Invalid or corrupted header bytes",
                    affected_approvals=APPROVAL_IMPACT_MAP[IssueType.INVALID_FILE]
                )
            )

        # 2. Virus & Security Scanner Check
        safe, risk_flags = SecurityScanner.scan_security_risks(file_bytes, filename)
        if not safe:
            for flag in risk_flags:
                issues.append(
                    ValidationErrorItem(
                        issue_type=IssueType.VIRUS_SECURITY_RISK,
                        severity=IssueSeverity.CRITICAL,
                        message=flag,
                        field_name="file_content",
                        affected_approvals=APPROVAL_IMPACT_MAP[IssueType.VIRUS_SECURITY_RISK]
                    )
                )

        # 3. Wrong Document Type Detection
        if expected_document_type and expected_document_type.upper() != "AUTO":
            exp_upper = expected_document_type.upper().replace(" ", "_")
            if classified_type and classified_type != "GENERAL_DOCUMENT":
                if classified_type != exp_upper and confidence >= 0.70:
                    issues.append(
                        ValidationErrorItem(
                            issue_type=IssueType.WRONG_DOCUMENT_TYPE,
                            severity=IssueSeverity.CRITICAL,
                            message=(
                                f"Wrong document type detected! Uploaded file is classified as '{classified_type}' "
                                f"(Confidence: {int(confidence * 100)}%), but expected category was '{exp_upper}'."
                            ),
                            field_name="document_type",
                            expected_value=exp_upper,
                            actual_value=classified_type,
                            affected_approvals=APPROVAL_IMPACT_MAP[IssueType.WRONG_DOCUMENT_TYPE]
                        )
                    )

        # Extract data if not provided
        if not extracted_data:
            text = OCRService.extract_text_from_file(file_bytes, mime_type, filename)
            extracted_data = OCRService.extract_metadata(text, expected_document_type)

        # 4. Expiry Date Check
        expiry_str = extracted_data.get("expiry_date")
        if expiry_str:
            expiry_dt = OCRService.parse_date_string(expiry_str)
            if expiry_dt and expiry_dt < datetime.datetime.utcnow():
                issues.append(
                    ValidationErrorItem(
                        issue_type=IssueType.EXPIRED_DOCUMENT,
                        severity=IssueSeverity.CRITICAL,
                        message=f"Document has expired! Expiration date was {expiry_str}.",
                        field_name="expiry_date",
                        expected_value="Date in the future",
                        actual_value=expiry_str,
                        affected_approvals=APPROVAL_IMPACT_MAP[IssueType.EXPIRED_DOCUMENT]
                    )
                )

        # 5. Missing Mandatory Structured Fields
        doc_num = extracted_data.get("document_number")
        doc_type_clean = (expected_document_type or classified_type or "").upper()

        if doc_type_clean == "PAN_CARD" and not doc_num:
            issues.append(
                ValidationErrorItem(
                    issue_type=IssueType.MISSING_IMPORTANT_FIELDS,
                    severity=IssueSeverity.WARNING,
                    message="PAN Card is missing a legible 10-character Permanent Account Number (e.g. ABCDE1234F).",
                    field_name="document_number",
                    expected_value="10-character PAN string",
                    actual_value="Not Found",
                    affected_approvals=["GST_REGISTRATION", "FSSAI_LICENSE"]
                )
            )
        elif doc_type_clean in ["GST_CERTIFICATE", "GST_IN"] and not doc_num:
            issues.append(
                ValidationErrorItem(
                    issue_type=IssueType.MISSING_IMPORTANT_FIELDS,
                    severity=IssueSeverity.WARNING,
                    message="GST Certificate is missing a legible 15-character GSTIN number.",
                    field_name="document_number",
                    expected_value="15-character GSTIN string",
                    actual_value="Not Found",
                    affected_approvals=["GST_REGISTRATION", "WATER_CONSENT"]
                )
            )

        is_valid = len([i for i in issues if i.severity == IssueSeverity.CRITICAL]) == 0

        return DocumentValidationResult(
            document_id=doc_id,
            file_name=filename,
            document_type=expected_document_type or classified_type or "UNKNOWN",
            is_valid=is_valid,
            issues=issues,
            extracted_summary=extracted_data
        )

    @classmethod
    async def validate_cross_document_consistency(
        cls, db: AsyncSession, business_id: uuid.UUID
    ) -> List[ValidationErrorItem]:
        """
        Cross-document & Profile consistency engine:
        - Compares Business Profile Address (city, district, state) against Rent Agreement / GST Certificate extracted text.
        - Compares Business Entity Name against extracted names on PAN Card & GST Certificate.
        - Compares PAN Number on PAN Card against PAN characters (3..12) inside GSTIN on GST Certificate.
        """
        inconsistencies: List[ValidationErrorItem] = []

        # 1. Fetch Business Profile
        biz_result = await db.execute(select(Business).where(Business.id == business_id))
        business = biz_result.scalars().first()
        if not business:
            return inconsistencies

        # 2. Fetch Latest Active Documents
        from app.services.document_service import DocumentService
        docs = await DocumentService.list_business_documents(db, business_id, latest_only=True)
        docs_by_type = {d.document_type: d for d in docs}

        # Profile Address normalized
        profile_city = (business.city or "").strip().lower()
        profile_district = (business.district or "").strip().lower()
        profile_state = (business.state or "").strip().lower()

        # A. Address Consistency Check (Rent Agreement / Electricity Bill)
        rent_doc = docs_by_type.get("RENT_AGREEMENT")
        if rent_doc and rent_doc.extracted_data:
            raw_text = (rent_doc.extracted_data.get("raw_text_snippet") or "").lower()
            # Remove company name from text for address checking to avoid false positive matches
            biz_name_lower = (business.name or "").lower()
            text_without_biz_name = raw_text.replace(biz_name_lower, "")
            
            # Check if text mentions address/premises in a different city (e.g. Mumbai, Thane, etc.)
            other_cities = ["mumbai", "thane", "nashik", "nagpur", "delhi", "bangalore", "hyderabad", "chennai", "kolkata"]
            detected_other = [c for c in other_cities if c in text_without_biz_name and c != profile_city]

            # If other city detected in premises address and registered profile city not in address text
            if detected_other or (profile_city not in text_without_biz_name and "address" in raw_text):
                detected_str = ", ".join([c.title() for c in detected_other]) if detected_other else "Different City/District"

                inconsistencies.append(
                    ValidationErrorItem(
                        issue_type=IssueType.ADDRESS_MISMATCH,
                        severity=IssueSeverity.CRITICAL,
                        message=(
                            f"ADDRESS MISMATCH DETECTED! Business Profile registered city is '{business.city}', "
                            f"but Rental Agreement premises specifies address in '{detected_str}'."
                        ),
                        field_name="address",
                        expected_value=f"{business.city}, {business.state}",
                        actual_value=detected_str,
                        affected_approvals=APPROVAL_IMPACT_MAP[IssueType.ADDRESS_MISMATCH]
                    )
                )

        # B. Legal Entity Name Consistency Check
        biz_name_clean = re.sub(r'[^a-zA-Z0-9]', '', business.name.lower())
        pan_doc = docs_by_type.get("PAN_CARD")
        if pan_doc and pan_doc.extracted_data.get("entity_name"):
            pan_name = pan_doc.extracted_data["entity_name"]
            pan_name_clean = re.sub(r'[^a-zA-Z0-9]', '', pan_name.lower())
            
            # Check prefix similarity or substring match
            if len(biz_name_clean) >= 4 and len(pan_name_clean) >= 4:
                if biz_name_clean[:4] not in pan_name_clean and pan_name_clean[:4] not in biz_name_clean:
                    inconsistencies.append(
                        ValidationErrorItem(
                            issue_type=IssueType.NAME_MISMATCH,
                            severity=IssueSeverity.WARNING,
                            message=(
                                f"ENTITY NAME MISMATCH! Business Profile name is '{business.name}', "
                                f"but PAN Card extracted name is '{pan_name}'."
                            ),
                            field_name="entity_name",
                            expected_value=business.name,
                            actual_value=pan_name,
                            affected_approvals=APPROVAL_IMPACT_MAP[IssueType.NAME_MISMATCH]
                        )
                    )

        # C. PAN vs GSTIN Cross-Check
        gst_doc = docs_by_type.get("GST_CERTIFICATE") or docs_by_type.get("GST_IN")
        if pan_doc and gst_doc:
            pan_number = pan_doc.extracted_data.get("document_number")
            gstin_number = gst_doc.extracted_data.get("document_number")

            if pan_number and gstin_number and len(gstin_number) == 15:
                # GSTIN chars 2 to 12 contains PAN number (0-indexed: gstin[2:12])
                gst_pan_part = gstin_number[2:12]
                if pan_number.upper() != gst_pan_part.upper():
                    inconsistencies.append(
                        ValidationErrorItem(
                            issue_type=IssueType.PAN_GSTIN_MISMATCH,
                            severity=IssueSeverity.CRITICAL,
                            message=(
                                f"PAN & GSTIN MISMATCH! PAN Card number is '{pan_number}', "
                                f"but GSTIN '{gstin_number}' contains embedded PAN '{gst_pan_part}'."
                            ),
                            field_name="pan_gstin",
                            expected_value=f"GSTIN embedded PAN matching {pan_number}",
                            actual_value=gstin_number,
                            affected_approvals=APPROVAL_IMPACT_MAP[IssueType.PAN_GSTIN_MISMATCH]
                        )
                    )

        return inconsistencies

    @classmethod
    async def generate_vault_validation_report(
        cls, db: AsyncSession, business_id: uuid.UUID
    ) -> VaultValidationReportOut:
        """
        Generate complete document validation audit report for a business vault:
        - Single document security & quality checks.
        - Cross-document consistency checks (Address, Name, PAN/GSTIN).
        - Missing required document checks.
        - Affected regulatory approvals mapping.
        - Vault health score (0 to 100).
        """
        # 1. Fetch Business Profile
        biz_result = await db.execute(select(Business).where(Business.id == business_id))
        business = biz_result.scalars().first()
        if not business:
            raise ValueError(f"Business profile {business_id} not found.")

        # 2. Get latest uploaded documents
        from app.services.document_service import DocumentService
        docs = await DocumentService.list_business_documents(db, business_id, latest_only=True)

        single_doc_results: List[DocumentValidationResult] = []
        expired_docs: List[str] = []

        total_issues = 0
        critical_issues = 0

        # Run single document validation for each stored file
        for doc in docs:
            try:
                from app.services.storage_service import StorageService
                file_bytes = StorageService.read_file(doc.storage_key)
            except Exception:
                file_bytes = b""

            res = cls.validate_single_document(
                file_bytes=file_bytes,
                filename=doc.file_name,
                mime_type=doc.mime_type,
                expected_document_type=doc.document_type,
                extracted_data=doc.extracted_data,
                classified_type=doc.document_type,
                confidence=doc.classification_confidence,
                doc_id=doc.id
            )
            single_doc_results.append(res)
            
            total_issues += len(res.issues)
            critical_issues += len([i for i in res.issues if i.severity == IssueSeverity.CRITICAL])

            if doc.expiry_date and doc.expiry_date < datetime.datetime.utcnow():
                expired_docs.append(f"{doc.document_type} (Expired: {doc.expiry_date.strftime('%Y-%m-%d')})")

        # 3. Cross-document consistency check
        cross_doc_inconsistencies = await cls.validate_cross_document_consistency(db, business_id)
        total_issues += len(cross_doc_inconsistencies)
        critical_issues += len([i for i in cross_doc_inconsistencies if i.severity == IssueSeverity.CRITICAL])

        # 4. Vault completeness & missing document check
        compliance = await DocumentService.check_business_vault_compliance(db, business_id)
        missing_docs = [item.document_type_name for item in compliance.items if not item.is_uploaded]

        # 5. Affected Approvals Impact Summary
        affected_map: Dict[str, List[str]] = {}
        all_issues = []
        for r in single_doc_results:
            all_issues.extend(r.issues)
        all_issues.extend(cross_doc_inconsistencies)

        for issue in all_issues:
            for app_code in issue.affected_approvals:
                affected_map.setdefault(app_code, []).append(issue.message)

        # 6. Calculate Health Score (100 base, -20 per critical, -10 per warning, -15 per missing doc)
        health_penalty = (critical_issues * 20) + ((total_issues - critical_issues) * 10) + (len(missing_docs) * 15)
        vault_health_score = max(0, 100 - health_penalty)

        overall_valid = (critical_issues == 0) and (len(missing_docs) == 0)

        return VaultValidationReportOut(
            business_id=business_id,
            business_name=business.name,
            overall_valid=overall_valid,
            vault_health_score=vault_health_score,
            total_documents_checked=len(docs),
            total_issues_found=total_issues,
            missing_documents=missing_docs,
            expired_documents=expired_docs,
            single_doc_results=single_doc_results,
            cross_doc_inconsistencies=cross_doc_inconsistencies,
            affected_approvals_summary=affected_map
        )
