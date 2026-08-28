import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.workflows import ApprovalStatus, IntegrationMode


class StatusUpdateSchema(BaseModel):
    status: ApprovalStatus = Field(..., description="Target status for the approval")
    notes: Optional[str] = Field(None, description="Optional transition notes")


class BusinessApprovalOut(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    business_id: uuid.UUID
    rule_code: str
    name: str
    category: str
    responsible_authority: str
    status: ApprovalStatus
    
    # Module 8 & 9 fields
    external_system: Optional[str] = None
    external_reference_id: Optional[str] = None
    integration_mode: str
    official_portal_url: Optional[str] = None
    
    sla_days: int
    sla_deadline: Optional[datetime] = None
    started_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    stage_history: List[Dict[str, Any]] = []
    additional_metadata: Dict[str, Any] = {}
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowHandoffResponse(BaseModel):
    approval_id: uuid.UUID
    workflow_id: uuid.UUID
    rule_code: str
    approval_name: str
    status: ApprovalStatus
    external_system: str
    integration_mode: str
    official_portal_url: str
    handoff_instructions: str
    prefilled_payload_summary: Dict[str, Any]


class WorkflowSubmitResponse(BaseModel):
    approval_id: uuid.UUID
    workflow_id: uuid.UUID
    rule_code: str
    approval_name: str
    status: ApprovalStatus
    external_system: str
    external_reference_id: str
    integration_mode: str
    official_portal_url: Optional[str] = None
    sla_deadline: Optional[datetime] = None
    submission_notes: str


class AdapterStatusSyncResponse(BaseModel):
    approval_id: uuid.UUID
    external_reference_id: str
    external_system: str
    current_status: ApprovalStatus
    remarks: str
    official_portal_url: Optional[str] = None
    synced_at: datetime


class AdapterInfoOut(BaseModel):
    system_name: str
    integration_mode: str
    official_portal_url: str
