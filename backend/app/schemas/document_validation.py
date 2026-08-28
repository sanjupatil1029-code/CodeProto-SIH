import uuid
import enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class IssueType(str, enum.Enum):
    INVALID_FILE = "INVALID_FILE"
    VIRUS_SECURITY_RISK = "VIRUS_SECURITY_RISK"
    WRONG_DOCUMENT_TYPE = "WRONG_DOCUMENT_TYPE"
    EXPIRED_DOCUMENT = "EXPIRED_DOCUMENT"
    MISSING_IMPORTANT_FIELDS = "MISSING_IMPORTANT_FIELDS"
    ADDRESS_MISMATCH = "ADDRESS_MISMATCH"
    NAME_MISMATCH = "NAME_MISMATCH"
    PAN_GSTIN_MISMATCH = "PAN_GSTIN_MISMATCH"
    MISSING_REQUIRED_DOCUMENT = "MISSING_REQUIRED_DOCUMENT"


class IssueSeverity(str, enum.Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"


class ValidationErrorItem(BaseModel):
    issue_type: IssueType
    severity: IssueSeverity
    message: str
    field_name: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    affected_approvals: List[str] = []


class DocumentValidationResult(BaseModel):
    document_id: Optional[uuid.UUID] = None
    file_name: str
    document_type: str
    is_valid: bool
    issues: List[ValidationErrorItem] = []
    extracted_summary: Dict[str, Any] = {}


class VaultValidationReportOut(BaseModel):
    business_id: uuid.UUID
    business_name: str
    overall_valid: bool
    vault_health_score: int
    total_documents_checked: int
    total_issues_found: int
    missing_documents: List[str] = []
    expired_documents: List[str] = []
    single_doc_results: List[DocumentValidationResult] = []
    cross_doc_inconsistencies: List[ValidationErrorItem] = []
    affected_approvals_summary: Dict[str, List[str]] = {}
