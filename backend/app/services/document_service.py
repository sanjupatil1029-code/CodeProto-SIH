import uuid
import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile, HTTPException, status

from app.models.document import Document, VerificationStatus
from app.models.rules import DocumentType
from app.schemas.document import (
    DocumentOut,
    DocumentUploadResponse,
    DocumentVerifyRequest,
    DocumentSignedUrlOut,
    DocumentVersionOut,
    VaultComplianceItem,
    VaultComplianceStatusOut,
)
from app.services.storage_service import StorageService
from app.services.ocr_service import OCRService
from app.services.rule_engine_service import RuleEngineService
from app.core.logging import logger

ALLOWED_MIME_TYPES = [
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
]


class DocumentService:

    @classmethod
    async def upload_document(
        cls,
        db: AsyncSession,
        business_id: uuid.UUID,
        uploaded_by: uuid.UUID,
        file: UploadFile,
        document_type: Optional[str] = None,
        expiry_date_override: Optional[datetime.datetime] = None,
    ) -> DocumentUploadResponse:
        """
        Upload document file, calculate SHA256 hash, run OCR text & metadata extraction,
        manage document versioning, store in object storage, and save metadata in DB.
        """
        filename = file.filename or "uploaded_doc.bin"
        content_type = file.content_type or "application/octet-stream"

        # Validate MIME type / extension
        ext = filename.lower().split(".")[-1]
        if content_type not in ALLOWED_MIME_TYPES and ext not in ["pdf", "png", "jpg", "jpeg"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{content_type}'. Allowed types: PDF, PNG, JPG/JPEG."
            )

        # Read file bytes
        file_bytes = await file.read()
        file_size = len(file_bytes)
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )

        # 1. Compute SHA-256 Hash
        file_hash = StorageService.compute_hash(file_bytes)

        # 2. Extract OCR text
        raw_text = OCRService.extract_text_from_file(file_bytes, content_type, filename)

        # 3. Classify document if type not explicitly provided
        classification_match = True
        if not document_type or document_type.upper() == "AUTO":
            classified_type, confidence = OCRService.classify_document(raw_text, filename)
            document_type = classified_type
        else:
            document_type = document_type.upper().replace(" ", "_")
            _, confidence = OCRService.classify_document(raw_text, filename)

        # 4. Extract structured metadata
        extracted_data = OCRService.extract_metadata(raw_text, document_type)

        # 4b. Run Document Validation Engine (Module 7)
        from app.services.validation_service import DocumentValidationService
        validation_res = DocumentValidationService.validate_single_document(
            file_bytes=file_bytes,
            filename=filename,
            mime_type=content_type,
            expected_document_type=document_type,
            extracted_data=extracted_data,
            classified_type=classified_type if not document_type or document_type.upper() == "AUTO" else document_type,
            confidence=confidence
        )
        extracted_data["validation_report"] = validation_res.model_dump(mode="json")

        # 5. Handle Expiry Date (Use override if provided, else use OCR extracted date)
        expiry_dt = expiry_date_override
        if not expiry_dt and extracted_data.get("expiry_date"):
            expiry_dt = OCRService.parse_date_string(extracted_data["expiry_date"])

        # 6. Version Management
        # Check existing documents for this business and document_type
        existing_result = await db.execute(
            select(Document)
            .where(
                and_(
                    Document.business_id == business_id,
                    Document.document_type == document_type,
                    Document.is_latest == True
                )
            )
        )
        existing_latest = existing_result.scalars().first()

        new_version = 1
        parent_id = None
        if existing_latest:
            new_version = existing_latest.version + 1
            parent_id = existing_latest.id
            # Mark previous version as not latest
            existing_latest.is_latest = False
            db.add(existing_latest)

        # 7. Generate Object Storage Key and Save File
        storage_key = StorageService.generate_storage_key(
            business_id=business_id,
            document_type=document_type,
            version=new_version,
            filename=filename
        )
        StorageService.save_file(file_bytes, storage_key)

        # 8. Evaluate Verification Status (incorporate validation result)
        if not validation_res.is_valid:
            verification_status = VerificationStatus.REJECTED
            critical_msg = "; ".join([i.message for i in validation_res.issues if i.severity == "CRITICAL"])
            v_reason = f"Validation Engine Rejected Document: {critical_msg}"
        else:
            v_status_str, v_reason = OCRService.evaluate_verification(extracted_data, confidence, expiry_dt)
            verification_status = VerificationStatus(v_status_str)

        # 9. Save Metadata to DB
        doc_record = Document(
            business_id=business_id,
            document_type=document_type,
            storage_key=storage_key,
            file_hash=file_hash,
            file_name=filename,
            mime_type=content_type,
            file_size=file_size,
            uploaded_by=uploaded_by,
            expiry_date=expiry_dt,
            verification_status=verification_status,
            verification_notes=v_reason,
            version=new_version,
            is_latest=True,
            parent_document_id=parent_id,
            extracted_data=extracted_data,
            classification_confidence=confidence,
            is_reusable=True
        )

        db.add(doc_record)
        await db.commit()
        await db.refresh(doc_record)

        logger.info(
            f"Document uploaded: ID {doc_record.id}, Type {document_type}, "
            f"Version {new_version}, Status {verification_status}"
        )

        return DocumentUploadResponse(
            document=DocumentOut.model_validate(doc_record),
            ocr_extracted=bool(extracted_data.get("document_number")),
            classification_match=classification_match,
            auto_verification_reason=v_reason
        )

    @classmethod
    async def get_document_by_id(cls, db: AsyncSession, document_id: uuid.UUID) -> Optional[Document]:
        """Fetch document model by ID."""
        result = await db.execute(select(Document).where(Document.id == document_id))
        return result.scalars().first()

    @classmethod
    async def list_business_documents(
        cls,
        db: AsyncSession,
        business_id: uuid.UUID,
        document_type: Optional[str] = None,
        verification_status: Optional[VerificationStatus] = None,
        latest_only: bool = True
    ) -> List[Document]:
        """Retrieve documents belonging to a business with flexible filters."""
        query = select(Document).where(Document.business_id == business_id)
        if latest_only:
            query = query.where(Document.is_latest == True)
        if document_type:
            query = query.where(Document.document_type == document_type.upper())
        if verification_status:
            query = query.where(Document.verification_status == verification_status)
        
        query = query.order_by(Document.uploaded_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    @classmethod
    async def get_document_versions(
        cls, db: AsyncSession, business_id: uuid.UUID, document_type: str
    ) -> List[DocumentVersionOut]:
        """Fetch version history of a specific document type for a business."""
        result = await db.execute(
            select(Document)
            .where(
                and_(
                    Document.business_id == business_id,
                    Document.document_type == document_type.upper()
                )
            )
            .order_by(Document.version.desc())
        )
        docs = result.scalars().all()
        return [
            DocumentVersionOut(
                id=d.id,
                version=d.version,
                file_name=d.file_name,
                file_hash=d.file_hash,
                uploaded_at=d.uploaded_at,
                verification_status=d.verification_status,
                is_latest=d.is_latest
            )
            for d in docs
        ]

    @classmethod
    async def verify_document(
        cls,
        db: AsyncSession,
        document_id: uuid.UUID,
        schema: DocumentVerifyRequest
    ) -> Document:
        """Update verification status (Officer / Admin review)."""
        doc = await cls.get_document_by_id(db, document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        doc.verification_status = schema.verification_status
        if schema.verification_notes:
            doc.verification_notes = schema.verification_notes

        doc.updated_at = datetime.datetime.utcnow()
        db.add(doc)
        await db.commit()
        await db.refresh(doc)

        logger.info(f"Document {document_id} verification updated to {schema.verification_status}")
        return doc

    @classmethod
    async def generate_signed_url(
        cls,
        db: AsyncSession,
        document_id: uuid.UUID,
        user_id: uuid.UUID,
        base_url: str,
        expires_in_seconds: int = 300
    ) -> DocumentSignedUrlOut:
        """Generate cryptographically signed download URL for document."""
        doc = await cls.get_document_by_id(db, document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        token, expires_at = StorageService.generate_signed_token(
            document_id=doc.id,
            user_id=user_id,
            expires_in_seconds=expires_in_seconds
        )

        signed_url = f"{base_url.rstrip('/')}/api/v1/documents/download-signed/{token}"

        return DocumentSignedUrlOut(
            document_id=doc.id,
            file_name=doc.file_name,
            mime_type=doc.mime_type,
            signed_url=signed_url,
            expires_in_seconds=expires_in_seconds,
            expires_at=expires_at
        )

    @classmethod
    async def re_ocr_document(cls, db: AsyncSession, document_id: uuid.UUID) -> Document:
        """Re-run text extraction & metadata OCR engine on an existing document."""
        doc = await cls.get_document_by_id(db, document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )

        file_bytes = StorageService.read_file(doc.storage_key)
        raw_text = OCRService.extract_text_from_file(file_bytes, doc.mime_type, doc.file_name)
        classified_type, confidence = OCRService.classify_document(raw_text, doc.file_name)
        extracted = OCRService.extract_metadata(raw_text, doc.document_type)

        doc.extracted_data = extracted
        doc.classification_confidence = confidence
        
        # Check expiry
        if extracted.get("expiry_date"):
            parsed_exp = OCRService.parse_date_string(extracted["expiry_date"])
            if parsed_exp:
                doc.expiry_date = parsed_exp

        v_status_str, v_reason = OCRService.evaluate_verification(extracted, confidence, doc.expiry_date)
        if doc.verification_status == VerificationStatus.PENDING:
            doc.verification_status = VerificationStatus(v_status_str)
            doc.verification_notes = f"Re-OCR: {v_reason}"

        doc.updated_at = datetime.datetime.utcnow()
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        return doc

    @classmethod
    async def check_business_vault_compliance(
        cls, db: AsyncSession, business_id: uuid.UUID
    ) -> VaultComplianceStatusOut:
        """
        Cross-reference required document types from applicable approval rules against business documents.
        Determines overall compliance and missing/expired documents.
        """
        # 1. Run rule engine to see applicable rules
        rule_evals = await RuleEngineService.evaluate_business_approvals(db, business_id)

        # 2. Collect mapping of document_type -> rules requiring it
        doc_type_rules: dict = {}
        for r in rule_evals:
            if r.status in ["APPLICABLE", "NEEDS_MORE_INFO"]:
                for dt in r.required_document_types:
                    doc_type_rules.setdefault(dt, []).append(r.rule_code)

        # 3. Get document types descriptions from DB
        doc_types_result = await db.execute(select(DocumentType))
        doc_type_names = {dt.code: dt.name for dt in doc_types_result.scalars().all()}

        # 4. Get latest uploaded documents for this business
        latest_docs = await cls.list_business_documents(db, business_id, latest_only=True)
        docs_by_type = {d.document_type: d for d in latest_docs}

        # Handle mapping variations (e.g. GST_IN -> GST_CERTIFICATE)
        if "GST_CERTIFICATE" in docs_by_type and "GST_IN" not in docs_by_type:
            docs_by_type["GST_IN"] = docs_by_type["GST_CERTIFICATE"]

        items: List[VaultComplianceItem] = []
        total_required = len(doc_type_rules)
        total_uploaded = 0
        total_verified = 0

        now = datetime.datetime.utcnow()

        for code, rules in doc_type_rules.items():
            name = doc_type_names.get(code, code.replace("_", " ").title())
            doc = docs_by_type.get(code)

            is_uploaded = doc is not None
            is_verified = False
            is_expired = False

            if doc:
                total_uploaded += 1
                if doc.expiry_date and doc.expiry_date < now:
                    is_expired = True

                if doc.verification_status in [VerificationStatus.VERIFIED, VerificationStatus.AUTO_VERIFIED] and not is_expired:
                    is_verified = True
                    total_verified += 1

            items.append(
                VaultComplianceItem(
                    document_type_code=code,
                    document_type_name=name,
                    required_for_rules=rules,
                    is_uploaded=is_uploaded,
                    is_verified=is_verified,
                    document_id=doc.id if doc else None,
                    verification_status=doc.verification_status if doc else None,
                    expiry_date=doc.expiry_date if doc else None,
                    is_expired=is_expired
                )
            )

        comp_pct = (total_verified / total_required * 100.0) if total_required > 0 else 100.0
        is_fully_compliant = (total_verified == total_required) and (total_required > 0)

        return VaultComplianceStatusOut(
            business_id=business_id,
            total_required=total_required,
            total_uploaded=total_uploaded,
            total_verified=total_verified,
            is_fully_compliant=is_fully_compliant,
            completion_percentage=round(comp_pct, 1),
            items=items
        )
