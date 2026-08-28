import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.regulatory_update import UpdateStatus


class RegulatoryUpdateCreateSchema(BaseModel):
    title: str = Field(..., description="Gazette notification or circular update title")
    source_authority: str = Field(..., description="Issuing authority (e.g. FSSAI Central Ministry, MPCB)")
    rule_code: str = Field(..., description="Target rule code being updated (e.g. FSSAI_LICENSE, FIRE_NOC)")
    summary: str = Field(..., description="Summary of statutory rule changes")
    extracted_changes: Dict[str, Any] = Field(..., description="AI-extracted rule comparison diff (old vs new values)")
    impact_summary: str = Field(..., description="Impact description on existing business roadmaps")


class RegulatoryUpdateReviewSchema(BaseModel):
    approve: bool = Field(..., description="True to approve & deploy new rule version, False to reject")
    review_notes: Optional[str] = Field(None, description="Admin review notes")


class RegulatoryUpdateOut(BaseModel):
    id: uuid.UUID
    title: str
    source_authority: str
    rule_code: str
    summary: str
    extracted_changes: Dict[str, Any]
    impact_summary: str
    status: UpdateStatus
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RuleVersionItemOut(BaseModel):
    rule_id: uuid.UUID
    rule_code: str
    rule_version: str
    name: str
    sla_days: int
    is_latest: bool
    status: str
    effective_from: datetime
    effective_to: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RuleVersionHistoryOut(BaseModel):
    rule_code: str
    name: str
    versions_count: int
    versions: List[RuleVersionItemOut]
