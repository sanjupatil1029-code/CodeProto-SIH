from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from app.models.rules import RuleStatus, JurisdictionType, ApprovalCategory


class DocumentTypeBase(BaseModel):
    code: str = Field(..., max_length=50, examples=["PAN_CARD"])
    name: str = Field(..., max_length=255, examples=["PAN Card of Business"])
    description: Optional[str] = Field(None, examples=["Permanent Account Number card issued by the Income Tax Department"])


class DocumentTypeCreate(DocumentTypeBase):
    pass


class DocumentTypeOut(DocumentTypeBase):
    created_at: datetime

    class Config:
        from_attributes = True


class ApprovalRuleBase(BaseModel):
    code: str = Field(..., max_length=100, examples=["FSSAI_LICENSE"])
    name: str = Field(..., max_length=255, examples=["FSSAI Food License"])
    category: ApprovalCategory = Field(default=ApprovalCategory.LICENSE)
    jurisdiction: JurisdictionType = Field(default=JurisdictionType.CENTRAL)
    state: Optional[str] = Field(None, max_length=100, examples=["Maharashtra"])
    responsible_authority: str = Field(..., max_length=255, examples=["Food Safety and Standards Authority of India"])
    sla_days: int = Field(default=30, gt=0, examples=[30])
    inspection_required: bool = Field(default=False)
    renewal_required: bool = Field(default=False)
    renewal_interval_months: Optional[int] = Field(None, gt=0, examples=[12])
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Nested recursive logic for evaluating rules")
    required_document_types: List[str] = Field(default_factory=list, description="List of document codes needed")
    dependencies: List[str] = Field(default_factory=list, description="List of approval codes required before this")
    explanation: Optional[str] = Field(None, description="Human-readable explanation of why this is required")
    version: str = Field(default="1.0.0", max_length=20, examples=["1.0.0"])
    status: RuleStatus = Field(default=RuleStatus.ACTIVE)
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    effective_to: Optional[datetime] = None


class ApprovalRuleCreate(ApprovalRuleBase):
    pass


class ApprovalRuleUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[ApprovalCategory] = None
    jurisdiction: Optional[JurisdictionType] = None
    state: Optional[str] = None
    responsible_authority: Optional[str] = None
    sla_days: Optional[int] = None
    inspection_required: Optional[bool] = None
    renewal_required: Optional[bool] = None
    renewal_interval_months: Optional[int] = None
    conditions: Optional[Dict[str, Any]] = None
    required_document_types: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    explanation: Optional[str] = None
    version: Optional[str] = None
    status: Optional[RuleStatus] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class ApprovalRuleOut(ApprovalRuleBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RuleEvaluationResult(BaseModel):
    rule_code: str
    name: str
    category: ApprovalCategory
    responsible_authority: str
    status: str  # APPLICABLE, NOT_APPLICABLE, NEEDS_MORE_INFO
    explanation: str
    sla_days: int
    inspection_required: bool
    required_document_types: List[str]
    dependencies: List[str]
    missing_fields: List[str] = Field(default_factory=list, description="Fields referenced in rules but missing in business profile")
