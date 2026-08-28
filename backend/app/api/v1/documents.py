import uuid
import datetime
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Query,
    Request,
    Response,
    status
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.auth import User, UserRole
from app.models.document import VerificationStatus
from app.schemas.document import (
    DocumentOut,
    DocumentUploadResponse,
    DocumentVerifyRequest,
    DocumentSignedUrlOut,
    DocumentVersionOut,
    VaultComplianceStatusOut,
)
from app.schemas.document_validation import (
    VaultValidationReportOut,
    DocumentValidationResult,
)
from app.services.auth_service import get_current_user
from app.services.business_service import BusinessService
from app.services.document_service import DocumentService
from app.services.storage_service import StorageService

router = APIRouter(prefix="/documents", tags=["Smart Document Vault"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    business_id: uuid.UUID = Form(...),
    document_type: Optional[str] = Form(None),
    expiry_date: Optional[str] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document (PDF, PNG, JPG) to the Smart Document Vault.
    Performs SHA-256 hash calculation, automated OCR text extraction, 
    document classification, expiry detection, and version control.
    """
    # Permission check: User must own the business or be OFFICER/ADMIN
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    if business.owner_id != current_user.id and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to upload documents for this business profile"
        )

    # Parse optional expiry date
    parsed_expiry = None
    if expiry_date:
        try:
            parsed_expiry = datetime.datetime.fromisoformat(expiry_date.replace("Z", "+00:00"))
        except ValueError:
            pass

    return await DocumentService.upload_document(
        db=db,
        business_id=business_id,
        uploaded_by=current_user.id,
        file=file,
        document_type=document_type,
        expiry_date_override=parsed_expiry
    )


@router.get("/business/{business_id}", response_model=List[DocumentOut])
async def list_business_documents(
    business_id: uuid.UUID,
    document_type: Optional[str] = Query(None, description="Filter by document type (e.g. PAN_CARD)"),
    verification_status: Optional[VerificationStatus] = Query(None, description="Filter by verification status"),
    latest_only: bool = Query(True, description="Retrieve latest document versions only"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve documents belonging to a business.
    Allows filtering by type, verification status, and latest version flag.
    """
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    if business.owner_id != current_user.id and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to business owner or officers"
        )

    docs = await DocumentService.list_business_documents(
        db=db,
        business_id=business_id,
        document_type=document_type,
        verification_status=verification_status,
        latest_only=latest_only
    )
    return docs


@router.get("/business/{business_id}/compliance", response_model=VaultComplianceStatusOut)
async def get_vault_compliance(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Check business vault compliance against required document types for active regulatory rules.
    Returns completeness percentage, missing documents, and verification statuses.
    """
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    if business.owner_id != current_user.id and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return await DocumentService.check_business_vault_compliance(db, business_id)


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get metadata, OCR extracted fields, and status of a specific document."""
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    business = await BusinessService.get_business_by_id(db, doc.business_id)
    if business and business.owner_id != current_user.id and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return doc


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Securely stream document file bytes directly to authenticated user.
    Prevents exposure of internal storage keys or raw file URLs.
    """
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    business = await BusinessService.get_business_by_id(db, doc.business_id)
    if business and business.owner_id != current_user.id and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    try:
        file_bytes = StorageService.read_file(doc.storage_key)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File content missing in storage"
        )

    return Response(
        content=file_bytes,
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{doc.file_name}"',
            "Cache-Control": "private, max-age=3600"
        }
    )


@router.get("/{document_id}/signed-url", response_model=DocumentSignedUrlOut)
async def get_signed_download_url(
    document_id: uuid.UUID,
    request: Request,
    expires_in_seconds: int = Query(300, ge=30, le=86400, description="URL validity duration in seconds (30s to 24h)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a cryptographically signed HMAC download URL with an expiration period.
    Can be passed safely to frontends, mobile apps, or external previewers without exposing raw paths.
    """
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    business = await BusinessService.get_business_by_id(db, doc.business_id)
    if business and business.owner_id != current_user.id and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    base_url = str(request.base_url)
    return await DocumentService.generate_signed_url(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
        base_url=base_url,
        expires_in_seconds=expires_in_seconds
    )


@router.get("/download-signed/{signed_token}")
async def download_signed_document(
    signed_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Public signed download endpoint. Validates token signature and expiration period
    before serving document content securely.
    """
    try:
        payload = StorageService.verify_signed_token(signed_token)
        doc_id = uuid.UUID(payload["sub"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired signed URL: {str(e)}"
        )

    doc = await DocumentService.get_document_by_id(db, doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    try:
        file_bytes = StorageService.read_file(doc.storage_key)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File content missing in storage"
        )

    return Response(
        content=file_bytes,
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{doc.file_name}"',
            "Cache-Control": "private, no-cache"
        }
    )


@router.patch("/{document_id}/verify", response_model=DocumentOut)
async def verify_document(
    document_id: uuid.UUID,
    schema: DocumentVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update document verification status (VERIFIED or REJECTED) with review notes.
    Restricted to Officers and Admins.
    """
    if current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only government officers or admins can verify documents"
        )

    return await DocumentService.verify_document(db, document_id, schema)


@router.get("/business/{business_id}/type/{document_type}/versions", response_model=List[DocumentVersionOut])
async def get_document_version_history(
    business_id: uuid.UUID,
    document_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve version audit trail of a document type for a business profile.
    Shows previous versions, file hashes, upload timestamps, and status changes.
    """
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    if business.owner_id != current_user.id and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return await DocumentService.get_document_versions(db, business_id, document_type)


@router.post("/{document_id}/re-ocr", response_model=DocumentOut)
async def re_ocr_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Re-run text OCR extraction and classification on an uploaded document."""
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    business = await BusinessService.get_business_by_id(db, doc.business_id)
    if business and business.owner_id != current_user.id and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return await DocumentService.re_ocr_document(db, document_id)


@router.get("/business/{business_id}/validation-report", response_model=VaultValidationReportOut)
async def get_vault_validation_report(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Run full Document Validation Engine across business vault:
    - Single document security & quality validation.
    - Cross-document consistency checks (Address, Entity Name, PAN vs GSTIN).
    - Missing required document checks.
    - Affected regulatory approvals mapping.
    - Overall Vault Health Score (0 to 100).
    """
    business = await BusinessService.get_business_by_id(db, business_id)
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    if business.owner_id != current_user.id and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    from app.services.validation_service import DocumentValidationService
    return await DocumentValidationService.generate_vault_validation_report(db, business_id)


@router.post("/{document_id}/validate", response_model=DocumentValidationResult)
async def validate_single_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Run full validation checks on a single uploaded document."""
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    business = await BusinessService.get_business_by_id(db, doc.business_id)
    if business and business.owner_id != current_user.id and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    try:
        file_bytes = StorageService.read_file(doc.storage_key)
    except Exception:
        file_bytes = b""

    from app.services.validation_service import DocumentValidationService
    return DocumentValidationService.validate_single_document(
        file_bytes=file_bytes,
        filename=doc.file_name,
        mime_type=doc.mime_type,
        expected_document_type=doc.document_type,
        extracted_data=doc.extracted_data,
        classified_type=doc.document_type,
        confidence=doc.classification_confidence,
        doc_id=doc.id
    )


@router.post("/ai-validate/{document_id}")
async def ai_validate_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Run Gemini AI Document Assistant validation with DPDP PII security compliance,
    confidence scoring, and real-time Scheme Matcher update.
    """
    doc = await DocumentService.get_document_by_id(db, document_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    business = await BusinessService.get_business_by_id(db, doc.business_id)
    if business and business.owner_id != current_user.id and current_user.role not in [UserRole.OFFICER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    doc, report = await DocumentService.validate_document_with_ai(db, document_id)
    return {
        "document": doc,
        "ai_report": report
    }

