import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.grievance import GrievanceCategory, GrievancePriority, GrievanceStatus


class GrievanceCreateSchema(BaseModel):
    business_id: uuid.UUID = Field(..., description="Target business profile ID")
    approval_id: Optional[uuid.UUID] = Field(None, description="Associated approval ID if grievance is regarding a specific license/SLA")
    title: str = Field(..., description="Grievance summary title")
    description: str = Field(..., description="Detailed description of issue or SLA delay")
    category: GrievanceCategory = Field(GrievanceCategory.SLA_BREACH, description="Category of grievance")
    priority: GrievancePriority = Field(GrievancePriority.MEDIUM, description="Priority level")
    department: Optional[str] = Field("General Authority", description="Target government department")


class GrievanceAssignSchema(BaseModel):
    officer_id: uuid.UUID = Field(..., description="Assigned officer ID")


class GrievanceResolveSchema(BaseModel):
    resolution_notes: str = Field(..., description="Official resolution notes and resolution actions taken")


class GrievanceOut(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    approval_id: Optional[uuid.UUID] = None
    complainant_id: uuid.UUID
    assigned_officer_id: Optional[uuid.UUID] = None
    title: str
    description: str
    department: str
    category: GrievanceCategory
    priority: GrievancePriority
    status: GrievanceStatus
    escalation_level: int
    resolution_deadline: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    escalation_history: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
