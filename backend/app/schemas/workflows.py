import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.models.workflows import ApprovalStatus


class StatusUpdateSchema(BaseModel):
    status: ApprovalStatus = Field(..., description="Target status for the approval")


class BusinessApprovalOut(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    rule_code: str
    name: str
    category: str
    responsible_authority: str
    status: ApprovalStatus
    sla_days: int
    sla_deadline: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
