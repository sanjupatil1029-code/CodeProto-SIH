import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict
from app.models.document import VerificationStatus


class DocumentBase(BaseModel):
    document_type: str
    expiry_date: Optional[datetime] = None


class DocumentOut(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    document_type: str
    storage_key: str
    file_hash: str
    file_name: str
    mime_type: str
    file_size: int
    uploaded_by: uuid.UUID
    uploaded_at: datetime
    expiry_date: Optional[datetime] = None
    verification_status: VerificationStatus
    verification_notes: Optional[str] = None
    version: int
    is_latest: bool
    parent_document_id: Optional[uuid.UUID] = None
    extracted_data: Dict[str, Any] = {}
    classification_confidence: float
    is_reusable: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    document: DocumentOut
    ocr_extracted: bool
    classification_match: bool
    auto_verification_reason: Optional[str] = None


class DocumentVerifyRequest(BaseModel):
    verification_status: VerificationStatus
    verification_notes: Optional[str] = None


class DocumentSignedUrlOut(BaseModel):
    document_id: uuid.UUID
    file_name: str
    mime_type: str
    signed_url: str
    expires_in_seconds: int
    expires_at: datetime


class DocumentVersionOut(BaseModel):
    id: uuid.UUID
    version: int
    file_name: str
    file_hash: str
    uploaded_at: datetime
    verification_status: VerificationStatus
    is_latest: bool


class VaultComplianceItem(BaseModel):
    document_type_code: str
    document_type_name: str
    required_for_rules: List[str]
    is_uploaded: bool
    is_verified: bool
    document_id: Optional[uuid.UUID] = None
    verification_status: Optional[VerificationStatus] = None
    expiry_date: Optional[datetime] = None
    is_expired: bool = False


class VaultComplianceStatusOut(BaseModel):
    business_id: uuid.UUID
    total_required: int
    total_uploaded: int
    total_verified: int
    is_fully_compliant: bool
    completion_percentage: float
    items: List[VaultComplianceItem]
