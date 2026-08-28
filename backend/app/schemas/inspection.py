import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.inspection import InspectionStatus


class InspectionScheduleSchema(BaseModel):
    approval_id: uuid.UUID = Field(..., description="Approval ID requiring inspection")
    title: str = Field(..., description="Title or type of inspection (e.g. FSSAI On-Site Hygiene Check)")
    scheduled_date: datetime = Field(..., description="Date and time scheduled for inspection")
    location_address: Optional[str] = Field(None, description="Premises address for inspection")
    officer_id: Optional[uuid.UUID] = Field(None, description="Assigned officer ID")


class InspectionRescheduleSchema(BaseModel):
    new_scheduled_date: datetime = Field(..., description="New requested inspection date")
    reason: str = Field(..., description="Reason for rescheduling")


class InspectionReportSchema(BaseModel):
    status: InspectionStatus = Field(..., description="Result status: COMPLETED or FAILED")
    inspector_notes: Optional[str] = Field(None, description="Detailed officer inspection notes")
    findings_summary: Optional[str] = Field(None, description="Summary of statutory findings")
    checklist_results: List[Dict[str, Any]] = Field([], description="List of checklist item evaluations")


class InspectionOut(BaseModel):
    id: uuid.UUID
    business_id: uuid.UUID
    approval_id: uuid.UUID
    officer_id: Optional[uuid.UUID] = None
    title: str
    status: InspectionStatus
    scheduled_date: Optional[datetime] = None
    actual_inspection_date: Optional[datetime] = None
    location_address: Optional[str] = None
    inspector_notes: Optional[str] = None
    findings_summary: Optional[str] = None
    checklist_results: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
